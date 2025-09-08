"""
Feedback Campaign API endpoints
Handles CSV upload, campaign management, and scheduling
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import pandas as pd
import io

from ..services.csv_processor import CSVProcessor
from ..services.feedback_scheduler import FeedbackScheduler
from ..repositories.campaign_repository import CampaignRepository
from ..schemas import (
    CampaignCreate,
    CampaignResponse,
    CampaignMetrics,
    ExperimentConfig,
    ScheduleParameters
)

router = APIRouter(prefix="/api/feedback-campaigns", tags=["feedback-campaigns"])

csv_processor = CSVProcessor()
feedback_scheduler = FeedbackScheduler()
campaign_repo = CampaignRepository()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_csv(
    file: UploadFile = File(...),
    campaign_name: str = None,
    restaurant_id: UUID = None
):
    """
    Upload CSV file with customer phone numbers and visit timestamps
    Max file size: 10MB, Max rows: 10,000
    Uses streaming processing for large files
    """
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted"
        )
    
    try:
        contents = await file.read()
        
        # Quick validation to determine processing approach
        validation_result = await csv_processor.validate_csv_streaming(contents)
        if not validation_result['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result['errors']
            )
        
        processed_data = None
        
        # Use streaming for large files
        if validation_result.get('requires_streaming', False):
            # Process using streaming approach
            async for result in csv_processor.process_recipients_streaming(contents):
                if result['type'] == 'error':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result['message']
                    )
                elif result['type'] == 'completed':
                    processed_data = result
                    break
                # Progress updates could be sent to client via WebSocket in future
        else:
            # Use traditional approach for smaller files
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
            validation_result = csv_processor.validate_csv(df)
            if not validation_result['valid']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_result['errors']
                )
            processed_data = csv_processor.process_recipients(df)
        
        if not processed_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process CSV data"
            )
        
        # Create campaign
        campaign = await campaign_repo.create_campaign({
            'name': campaign_name or f"Campaign {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'restaurant_id': restaurant_id,
            'status': 'draft',
            'recipient_count': len(processed_data['recipients']),
            'settings': {
                'upload_filename': file.filename,
                'upload_timestamp': datetime.now().isoformat(),
                'file_size_bytes': file.size,
                'processing_method': 'streaming' if validation_result.get('requires_streaming') else 'standard'
            }
        })
        
        # Store recipients
        await campaign_repo.bulk_create_recipients(
            campaign['id'],
            processed_data['recipients']
        )
        
        return {
            'campaign_id': campaign['id'],
            'recipients_uploaded': len(processed_data['recipients']),
            'duplicates_removed': processed_data['duplicates_count'],
            'invalid_numbers': processed_data['invalid_count'],
            'validation_warnings': processed_data.get('warnings', []),
            'processing_method': 'streaming' if validation_result.get('requires_streaming') else 'standard',
            'file_size_mb': round(file.size / (1024 * 1024), 2)
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}"
        )


@router.post("/", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate):
    """Create a new feedback campaign"""
    try:
        result = await campaign_repo.create_campaign(campaign.dict())
        return CampaignResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating campaign: {str(e)}"
        )


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[str] = None,
    restaurant_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
):
    """List feedback campaigns with filtering"""
    filters = {}
    if status:
        filters['status'] = status
    if restaurant_id:
        filters['restaurant_id'] = restaurant_id
    if date_from and date_to:
        filters['date_range'] = (date_from, date_to)
    
    campaigns = await campaign_repo.list_campaigns(
        filters=filters,
        limit=limit,
        offset=offset
    )
    
    return [CampaignResponse(**c) for c in campaigns]


@router.post("/{campaign_id}/schedule")
async def schedule_campaign(
    campaign_id: UUID,
    schedule_params: ScheduleParameters
):
    """Schedule a campaign for sending"""
    try:
        # Verify campaign exists and is in draft status
        campaign = await campaign_repo.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        if campaign['status'] != 'draft':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign is {campaign['status']}, must be draft to schedule"
            )
        
        # Schedule the campaign
        scheduled_jobs = await feedback_scheduler.schedule_campaign(
            campaign_id,
            schedule_params.dict()
        )
        
        # Update campaign status
        await campaign_repo.update_campaign(
            campaign_id,
            {
                'status': 'scheduled',
                'scheduled_start': schedule_params.start_time,
                'scheduled_end': schedule_params.end_time,
                'settings': {
                    **campaign.get('settings', {}),
                    'schedule_params': schedule_params.dict(),
                    'scheduled_jobs': scheduled_jobs
                }
            }
        )
        
        return {
            'campaign_id': campaign_id,
            'status': 'scheduled',
            'scheduled_messages': len(scheduled_jobs),
            'start_time': schedule_params.start_time,
            'end_time': schedule_params.end_time
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling campaign: {str(e)}"
        )


@router.get("/{campaign_id}/metrics", response_model=CampaignMetrics)
async def get_campaign_metrics(campaign_id: UUID):
    """Get performance metrics for a campaign"""
    try:
        metrics = await campaign_repo.get_campaign_metrics(campaign_id)
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return CampaignMetrics(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )


@router.post("/{campaign_id}/experiments")
async def create_experiment(
    campaign_id: UUID,
    experiment: ExperimentConfig
):
    """Create an A/B test experiment for a campaign"""
    try:
        # Validate campaign exists
        campaign = await campaign_repo.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Validate variant weights sum to 1.0
        total_weight = sum(v.weight for v in experiment.variants)
        if abs(total_weight - 1.0) > 0.001:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Variant weights must sum to 1.0, got {total_weight}"
            )
        
        # Create experiment
        experiment_data = await campaign_repo.create_experiment(
            campaign_id,
            experiment.dict()
        )
        
        return {
            'experiment_id': experiment_data['id'],
            'campaign_id': campaign_id,
            'name': experiment.name,
            'variants': len(experiment.variants),
            'status': 'running'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating experiment: {str(e)}"
        )


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: UUID):
    """Soft delete a campaign"""
    try:
        result = await campaign_repo.soft_delete_campaign(campaign_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return {'message': 'Campaign deleted successfully'}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting campaign: {str(e)}"
        )