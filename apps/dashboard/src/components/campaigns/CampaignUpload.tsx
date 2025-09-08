/**
 * CSV Upload Component for Feedback Campaigns
 * Handles drag-and-drop file uploads with validation
 */

"use client";

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  X,
  Download
} from 'lucide-react';

interface UploadResult {
  campaign_id: string;
  recipients_uploaded: number;
  duplicates_removed: number;
  invalid_numbers: number;
  validation_warnings: string[];
}

interface CampaignUploadProps {
  onUploadSuccess?: (result: UploadResult) => void;
  onError?: (error: string) => void;
  restaurantId: string;
}

export default function CampaignUpload({
  onUploadSuccess,
  onError,
  restaurantId
}: CampaignUploadProps) {
  const [campaignName, setCampaignName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      handleFileUpload(acceptedFiles[0]);
    }
  }, []);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
    onError: (err) => setError(err.message),
  });
  
  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setUploadResult(null);
    
    try {
      // Validate file size
      if (file.size > 10 * 1024 * 1024) {
        throw new Error('الملف كبير جداً. الحد الأقصى 10 ميجابايت');
      }
      
      // Validate file type
      if (!file.name.endsWith('.csv')) {
        throw new Error('يجب أن يكون الملف من نوع CSV');
      }
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('restaurant_id', restaurantId);
      
      if (campaignName.trim()) {
        formData.append('campaign_name', campaignName.trim());
      }
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);
      
      const response = await fetch('/api/feedback-campaigns/upload', {
        method: 'POST',
        body: formData,
      });
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'فشل في رفع الملف');
      }
      
      const result: UploadResult = await response.json();
      setUploadResult(result);
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'حدث خطأ غير متوقع';
      setError(errorMessage);
      
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };
  
  const downloadSampleCSV = () => {
    const csvContent = `phone_number,visit_timestamp,customer_name,table_number
0501234567,2025-01-08 14:30:00,أحمد علي,5
+966502345678,2025-01-08 15:45:00,فاطمة حسن,12
966503456789,2025-01-08 19:20:00,محمد سالم,8`;
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'نموذج_قائمة_العملاء.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  const resetUpload = () => {
    setUploadResult(null);
    setError(null);
    setCampaignName('');
  };
  
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-right">
          رفع قائمة العملاء
        </CardTitle>
        <p className="text-sm text-muted-foreground text-right">
          ارفع ملف CSV يحتوي على أرقام هواتف العملاء وأوقات زياراتهم
        </p>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Campaign Name Input */}
        <div className="space-y-2">
          <Label htmlFor="campaign-name" className="text-right block">
            اسم الحملة (اختياري)
          </Label>
          <Input
            id="campaign-name"
            value={campaignName}
            onChange={(e) => setCampaignName(e.target.value)}
            placeholder="مثال: حملة تقييم شهر يناير"
            disabled={uploading}
            className="text-right"
          />
        </div>
        
        {/* Upload Area */}
        {!uploadResult && (
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragActive || dragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-border hover:border-primary/50'
              }
              ${uploading ? 'pointer-events-none opacity-50' : ''}
            `}
          >
            <input {...getInputProps()} />
            <div className="space-y-4">
              <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
              <div>
                <p className="text-lg font-medium">
                  {isDragActive 
                    ? 'أسقط الملف هنا...' 
                    : 'اسحب ملف CSV هنا أو انقر للاختيار'
                  }
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  الحد الأقصى: 10 ميجابايت • 10,000 سطر • تنسيق CSV فقط
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Upload Progress */}
        {uploading && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>جاري الرفع...</span>
              <span>{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} />
          </div>
        )}
        
        {/* Upload Success */}
        {uploadResult && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-right">
              <div className="space-y-2">
                <p className="font-medium text-green-800">
                  تم رفع الملف بنجاح!
                </p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">تم رفعهم:</span>
                    <span className="mr-2">{uploadResult.recipients_uploaded} عميل</span>
                  </div>
                  <div>
                    <span className="font-medium">مكرر:</span>
                    <span className="mr-2">{uploadResult.duplicates_removed}</span>
                  </div>
                  <div>
                    <span className="font-medium">أرقام غير صحيحة:</span>
                    <span className="mr-2">{uploadResult.invalid_numbers}</span>
                  </div>
                  <div>
                    <span className="font-medium">ID الحملة:</span>
                    <span className="mr-2 font-mono text-xs">
                      {uploadResult.campaign_id.slice(-8)}...
                    </span>
                  </div>
                </div>
                
                {uploadResult.validation_warnings.length > 0 && (
                  <div className="mt-3">
                    <p className="font-medium text-amber-700 mb-1">تنبيهات:</p>
                    <ul className="text-sm text-amber-600 space-y-1">
                      {uploadResult.validation_warnings.map((warning, index) => (
                        <li key={index} className="flex items-start">
                          <span className="mr-2">•</span>
                          <span>{warning}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </AlertDescription>
          </Alert>
        )}
        
        {/* Upload Error */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-right">
              {error}
            </AlertDescription>
          </Alert>
        )}
        
        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-4">
          <div className="space-x-2">
            {uploadResult && (
              <Button onClick={resetUpload} variant="outline">
                رفع ملف جديد
              </Button>
            )}
          </div>
          
          <Button 
            onClick={downloadSampleCSV}
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
          >
            <Download className="h-4 w-4 mr-2" />
            تحميل نموذج CSV
          </Button>
        </div>
        
        {/* Format Instructions */}
        <div className="bg-muted/50 rounded-lg p-4 space-y-2 text-sm">
          <h4 className="font-medium text-right">تنسيق الملف المطلوب:</h4>
          <ul className="space-y-1 text-muted-foreground text-right">
            <li>• <code>phone_number</code>: رقم الهاتف (مطلوب)</li>
            <li>• <code>visit_timestamp</code>: وقت الزيارة بصيغة YYYY-MM-DD HH:MM:SS (مطلوب)</li>
            <li>• <code>customer_name</code>: اسم العميل (اختياري)</li>
            <li>• <code>table_number</code>: رقم الطاولة (اختياري)</li>
          </ul>
          <p className="text-xs text-muted-foreground mt-2 text-right">
            الأعمدة الإضافية سيتم حفظها كبيانات إضافية مع العميل
          </p>
        </div>
      </CardContent>
    </Card>
  );
}