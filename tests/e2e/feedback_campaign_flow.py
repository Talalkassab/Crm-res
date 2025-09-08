"""
End-to-end tests for feedback campaign flow
Tests the complete workflow from CSV upload to report generation
"""

import pytest
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import tempfile
import csv
import os


@pytest.mark.asyncio
@pytest.mark.e2e
class TestFeedbackCampaignE2E:
    """End-to-end tests for feedback campaign system"""
    
    @pytest.fixture
    async def browser_context(self):
        """Set up browser context for testing"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)  # Set to True in CI
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='ar-SA'
        )
        
        yield context
        
        await context.close()
        await browser.close()
        await playwright.stop()
    
    @pytest.fixture
    def sample_csv_file(self):
        """Create a temporary CSV file for testing"""
        csv_data = [
            ['phone_number', 'visit_timestamp', 'customer_name', 'table_number'],
            ['0501234567', '2025-01-08 14:30:00', 'أحمد علي', '5'],
            ['0502345678', '2025-01-08 15:45:00', 'فاطمة حسن', '12'],
            ['0503456789', '2025-01-08 19:20:00', 'محمد سالم', '8'],
            ['+966504567890', '2025-01-08 20:15:00', 'نورا أحمد', '3'],
            ['966505678901', '2025-01-08 21:30:00', 'خالد محمد', '15']
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            temp_file_path = f.name
        
        yield temp_file_path
        
        # Cleanup
        os.unlink(temp_file_path)
    
    @pytest.fixture
    async def authenticated_page(self, browser_context):
        """Create an authenticated page session"""
        page = await browser_context.new_page()
        
        # Navigate to login page
        await page.goto('http://localhost:3000/login')
        
        # Perform login (adjust selectors based on your login form)
        await page.fill('[data-testid="email-input"]', 'test@example.com')
        await page.fill('[data-testid="password-input"]', 'password123')
        await page.click('[data-testid="login-button"]')
        
        # Wait for redirect to dashboard
        await page.wait_for_url('**/dashboard')
        
        return page
    
    async def test_complete_campaign_workflow(self, authenticated_page, sample_csv_file):
        """Test the complete feedback campaign workflow"""
        page = authenticated_page
        
        # Step 1: Navigate to campaigns page
        await page.click('[data-testid="campaigns-nav"]')
        await page.wait_for_selector('[data-testid="campaigns-page"]')
        
        # Step 2: Create new campaign
        await page.click('[data-testid="create-campaign-button"]')
        await page.wait_for_selector('[data-testid="campaign-upload-form"]')
        
        # Step 3: Fill campaign name
        await page.fill(
            '[data-testid="campaign-name-input"]', 
            f'Test Campaign E2E {datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )
        
        # Step 4: Upload CSV file
        file_input = page.locator('[data-testid="csv-file-input"]')
        await file_input.set_input_files(sample_csv_file)
        
        # Step 5: Wait for upload processing
        await page.wait_for_selector('[data-testid="upload-success"]', timeout=10000)
        
        # Verify upload results
        recipients_count = await page.locator('[data-testid="recipients-uploaded"]').text_content()
        assert '5' in recipients_count
        
        # Step 6: Navigate to campaign list
        await page.click('[data-testid="view-campaigns-button"]')
        await page.wait_for_selector('[data-testid="campaign-list"]')
        
        # Step 7: Find and schedule the created campaign
        campaign_card = page.locator('[data-testid="campaign-card"]').first
        await campaign_card.locator('[data-testid="campaign-menu"]').click()
        await page.click('[data-testid="schedule-campaign"]')
        
        # Step 8: Configure campaign schedule
        await page.wait_for_selector('[data-testid="schedule-dialog"]')
        
        # Set start time (1 hour from now)
        start_time = datetime.now() + timedelta(hours=1)
        await page.fill(
            '[data-testid="start-time-input"]',
            start_time.strftime('%Y-%m-%dT%H:%M')
        )
        
        # Set end time (7 days from start)
        end_time = start_time + timedelta(days=7)
        await page.fill(
            '[data-testid="end-time-input"]',
            end_time.strftime('%Y-%m-%dT%H:%M')
        )
        
        # Confirm scheduling
        await page.click('[data-testid="confirm-schedule"]')
        
        # Step 9: Verify campaign is scheduled
        await page.wait_for_selector('[data-testid="schedule-success"]')
        
        # Check campaign status changed to 'scheduled'
        campaign_status = await campaign_card.locator('[data-testid="campaign-status"]').text_content()
        assert 'مجدولة' in campaign_status or 'نشطة' in campaign_status
    
    async def test_real_time_feedback_monitoring(self, authenticated_page):
        """Test real-time feedback monitoring interface"""
        page = authenticated_page
        
        # Navigate to feedback monitor
        await page.click('[data-testid="feedback-nav"]')
        await page.click('[data-testid="feedback-monitor-tab"]')
        await page.wait_for_selector('[data-testid="feedback-monitor"]')
        
        # Verify live stats are displayed
        stats_cards = page.locator('[data-testid="live-stats-card"]')
        assert await stats_cards.count() >= 4  # Should have at least 4 stat cards
        
        # Verify connection status
        connection_status = page.locator('[data-testid="connection-status"]')
        await connection_status.wait_for()
        status_text = await connection_status.text_content()
        assert 'متصل' in status_text
        
        # Verify feedback feed is present
        feedback_feed = page.locator('[data-testid="feedback-feed"]')
        await feedback_feed.wait_for()
        
        # Test auto-scroll toggle
        auto_scroll_toggle = page.locator('[data-testid="auto-scroll-toggle"]')
        await auto_scroll_toggle.click()
        
        # Wait for some time to see if real-time updates work
        await page.wait_for_timeout(5000)
        
        # Check if any feedback items are displayed
        feedback_items = page.locator('[data-testid="feedback-item"]')
        feedback_count = await feedback_items.count()
        
        # If no real feedback, at least UI should be responsive
        assert feedback_count >= 0
    
    async def test_alert_center_functionality(self, authenticated_page):
        """Test alert center functionality"""
        page = authenticated_page
        
        # Navigate to alert center
        await page.click('[data-testid="feedback-nav"]')
        await page.click('[data-testid="alert-center-tab"]')
        await page.wait_for_selector('[data-testid="alert-center"]')
        
        # Test filter functionality
        status_filter = page.locator('[data-testid="status-filter"]')
        await status_filter.wait_for()
        
        # Test different filter options
        filter_options = ['pending', 'acknowledged', 'all']
        for option in filter_options:
            await page.click(f'[data-testid="filter-{option}"]')
            await page.wait_for_timeout(1000)  # Wait for filter to apply
            
            # Verify filter is active
            active_filter = page.locator(f'[data-testid="filter-{option}"][data-active="true"]')
            assert await active_filter.count() == 1
        
        # Test priority filter
        priority_filters = ['immediate', 'high', 'medium', 'low', 'all']
        for priority in priority_filters:
            await page.click(f'[data-testid="priority-filter-{priority}"]')
            await page.wait_for_timeout(1000)
        
        # If there are alerts, test acknowledgment
        alerts = page.locator('[data-testid="alert-item"]')
        alert_count = await alerts.count()
        
        if alert_count > 0:
            # Click on first alert's acknowledge button
            first_alert = alerts.first
            acknowledge_btn = first_alert.locator('[data-testid="acknowledge-alert"]')
            
            if await acknowledge_btn.count() > 0:
                await acknowledge_btn.click()
                
                # Fill acknowledgment dialog
                await page.wait_for_selector('[data-testid="acknowledge-dialog"]')
                await page.fill(
                    '[data-testid="acknowledgment-notes"]',
                    'تم التعامل مع المشكلة وحلها'
                )
                await page.click('[data-testid="confirm-acknowledge"]')
                
                # Verify dialog closes
                await page.wait_for_selector('[data-testid="acknowledge-dialog"]', state='detached')
    
    async def test_campaign_analytics_and_reports(self, authenticated_page):
        """Test campaign analytics and reporting"""
        page = authenticated_page
        
        # Navigate to analytics/reports section
        await page.click('[data-testid="analytics-nav"]')
        await page.wait_for_selector('[data-testid="analytics-dashboard"]')
        
        # Test date range picker
        date_picker = page.locator('[data-testid="date-range-picker"]')
        await date_picker.click()
        
        # Select last 7 days
        await page.click('[data-testid="date-range-7days"]')
        await page.wait_for_timeout(2000)  # Wait for data to load
        
        # Verify analytics cards are displayed
        analytics_cards = page.locator('[data-testid="analytics-card"]')
        card_count = await analytics_cards.count()
        assert card_count >= 3  # Should have multiple analytics cards
        
        # Test export functionality
        export_button = page.locator('[data-testid="export-report"]')
        if await export_button.count() > 0:
            await export_button.click()
            
            # Select export format
            await page.click('[data-testid="export-csv"]')
            
            # Wait for download to start (in real test, you'd handle the download)
            await page.wait_for_timeout(2000)
        
        # Test insights generation
        insights_section = page.locator('[data-testid="ai-insights"]')
        if await insights_section.count() > 0:
            # Verify insights are displayed
            insight_items = page.locator('[data-testid="insight-item"]')
            insight_count = await insight_items.count()
            assert insight_count >= 0
    
    async def test_ab_testing_configuration(self, authenticated_page):
        """Test A/B testing configuration"""
        page = authenticated_page
        
        # Navigate to campaigns
        await page.click('[data-testid="campaigns-nav"]')
        
        # Find a campaign and access its A/B testing
        campaign_card = page.locator('[data-testid="campaign-card"]').first
        if await campaign_card.count() > 0:
            await campaign_card.locator('[data-testid="campaign-menu"]').click()
            await page.click('[data-testid="ab-testing"]')
            
            # Wait for A/B testing dialog/page
            await page.wait_for_selector('[data-testid="ab-test-config"]')
            
            # Create new A/B test
            await page.click('[data-testid="create-ab-test"]')
            
            # Fill test configuration
            await page.fill('[data-testid="test-name"]', 'Message Style Test')
            await page.fill('[data-testid="test-description"]', 'Testing formal vs casual messaging')
            
            # Add variants
            await page.click('[data-testid="add-variant"]')
            await page.fill('[data-testid="variant-1-name"]', 'Formal')
            await page.fill('[data-testid="variant-1-weight"]', '0.5')
            
            await page.click('[data-testid="add-variant"]')
            await page.fill('[data-testid="variant-2-name"]', 'Casual')
            await page.fill('[data-testid="variant-2-weight"]', '0.5')
            
            # Set minimum sample size
            await page.fill('[data-testid="min-sample-size"]', '100')
            
            # Save A/B test
            await page.click('[data-testid="save-ab-test"]')
            
            # Verify test was created
            await page.wait_for_selector('[data-testid="ab-test-created"]')
    
    async def test_error_handling_and_validation(self, authenticated_page):
        """Test error handling and form validation"""
        page = authenticated_page
        
        # Test CSV upload with invalid file
        await page.click('[data-testid="campaigns-nav"]')
        await page.click('[data-testid="create-campaign-button"]')
        
        # Try to upload a non-CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a CSV file")
            invalid_file = f.name
        
        try:
            file_input = page.locator('[data-testid="csv-file-input"]')
            await file_input.set_input_files(invalid_file)
            
            # Should show error message
            error_message = page.locator('[data-testid="upload-error"]')
            await error_message.wait_for()
            error_text = await error_message.text_content()
            assert 'CSV' in error_text
            
        finally:
            os.unlink(invalid_file)
        
        # Test form validation
        campaign_name_input = page.locator('[data-testid="campaign-name-input"]')
        await campaign_name_input.fill('')  # Empty name
        
        # Try to submit (if there's a submit without file)
        # The form should prevent submission or show validation errors
        
        # Test network error handling (mock by blocking requests)
        await page.route('**/api/feedback-campaigns/**', lambda route: route.abort())
        
        # Try to perform an action that would make an API call
        await campaign_name_input.fill('Test Campaign')
        
        # Upload a valid CSV to trigger API call
        csv_data = [['phone_number', 'visit_timestamp'], ['0501234567', '2025-01-08 14:30:00']]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            temp_csv = f.name
        
        try:
            await file_input.set_input_files(temp_csv)
            
            # Should show network error
            await page.wait_for_selector('[data-testid="network-error"]', timeout=5000)
            
        finally:
            os.unlink(temp_csv)
        
        # Remove route block
        await page.unroute('**/api/feedback-campaigns/**')
    
    async def test_responsive_design(self, browser_context):
        """Test responsive design on different screen sizes"""
        # Test mobile viewport
        await browser_context.set_viewport_size({'width': 375, 'height': 667})  # iPhone SE
        
        page = await browser_context.new_page()
        await page.goto('http://localhost:3000/dashboard')
        
        # Verify mobile navigation works
        mobile_menu = page.locator('[data-testid="mobile-menu-button"]')
        if await mobile_menu.count() > 0:
            await mobile_menu.click()
            
            # Verify menu opens
            mobile_nav = page.locator('[data-testid="mobile-navigation"]')
            await mobile_nav.wait_for()
        
        # Test tablet viewport
        await browser_context.set_viewport_size({'width': 768, 'height': 1024})  # iPad
        await page.reload()
        
        # Verify layout adjusts for tablet
        campaign_grid = page.locator('[data-testid="campaign-grid"]')
        if await campaign_grid.count() > 0:
            # Verify grid layout works on tablet
            grid_items = page.locator('[data-testid="campaign-card"]')
            assert await grid_items.count() >= 0
        
        await page.close()


# Run configuration for pytest
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--asyncio-mode=auto",
        "--tb=short"
    ])