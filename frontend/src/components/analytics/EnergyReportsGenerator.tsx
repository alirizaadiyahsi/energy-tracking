import React, { useState, useMemo } from 'react';
import { 
  FileText, 
  Download, 
  Calendar, 
  Filter, 
  Settings, 
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  Mail,
  Printer,
  BarChart3,
  PieChart,
  TrendingUp,
  Activity
} from 'lucide-react';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  type: 'summary' | 'detailed' | 'comparison' | 'forecast';
  category: 'energy' | 'efficiency' | 'cost' | 'devices' | 'alerts';
  estimatedTime: string;
  lastGenerated?: string;
  icon: React.ReactNode;
}

interface ReportConfig {
  templateId: string;
  dateRange: {
    start: string;
    end: string;
    preset: string;
  };
  filters: {
    devices: string[];
    locations: string[];
    deviceTypes: string[];
  };
  format: 'pdf' | 'excel' | 'csv' | 'json';
  includeCharts: boolean;
  includeSummary: boolean;
  includeDetails: boolean;
  autoSchedule?: {
    enabled: boolean;
    frequency: 'daily' | 'weekly' | 'monthly';
    recipients: string[];
  };
}

interface GeneratedReport {
  id: string;
  name: string;
  templateName: string;
  generatedAt: string;
  status: 'generating' | 'completed' | 'failed';
  downloadUrl?: string;
  size?: string;
  format: string;
}

interface EnergyReportsGeneratorProps {
  showTemplateLibrary?: boolean;
  showScheduledReports?: boolean;
  compactMode?: boolean;
}

const EnergyReportsGenerator: React.FC<EnergyReportsGeneratorProps> = () => {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [reportConfig, setReportConfig] = useState<ReportConfig>({
    templateId: '',
    dateRange: {
      start: '',
      end: '',
      preset: 'last-30-days',
    },
    filters: {
      devices: [],
      locations: [],
      deviceTypes: [],
    },
    format: 'pdf',
    includeCharts: true,
    includeSummary: true,
    includeDetails: true,
    autoSchedule: {
      enabled: false,
      frequency: 'weekly',
      recipients: [],
    },
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState<'generate' | 'history' | 'scheduled'>('generate');

  // Report templates
  const reportTemplates: ReportTemplate[] = useMemo(() => [
    {
      id: 'energy-consumption-summary',
      name: 'Energy Consumption Summary',
      description: 'Overview of total energy consumption with trends and comparisons',
      type: 'summary',
      category: 'energy',
      estimatedTime: '2-3 minutes',
      lastGenerated: '2024-08-09T14:30:00Z',
      icon: <BarChart3 className="h-5 w-5" />,
    },
    {
      id: 'device-efficiency-report',
      name: 'Device Efficiency Analysis',
      description: 'Detailed efficiency metrics for all devices with recommendations',
      type: 'detailed',
      category: 'efficiency',
      estimatedTime: '3-5 minutes',
      lastGenerated: '2024-08-08T09:15:00Z',
      icon: <TrendingUp className="h-5 w-5" />,
    },
    {
      id: 'cost-analysis-report',
      name: 'Cost Analysis Report',
      description: 'Financial impact analysis with cost breakdowns and savings opportunities',
      type: 'detailed',
      category: 'cost',
      estimatedTime: '4-6 minutes',
      lastGenerated: '2024-08-07T16:45:00Z',
      icon: <PieChart className="h-5 w-5" />,
    },
    {
      id: 'comparative-performance',
      name: 'Comparative Performance',
      description: 'Side-by-side device and location performance comparisons',
      type: 'comparison',
      category: 'devices',
      estimatedTime: '3-4 minutes',
      icon: <Activity className="h-5 w-5" />,
    },
    {
      id: 'energy-forecast',
      name: 'Energy Forecast Report',
      description: 'Predictive analysis with consumption forecasts and recommendations',
      type: 'forecast',
      category: 'energy',
      estimatedTime: '5-7 minutes',
      icon: <TrendingUp className="h-5 w-5" />,
    },
    {
      id: 'alerts-incidents',
      name: 'Alerts & Incidents Summary',
      description: 'Comprehensive overview of system alerts, anomalies, and incidents',
      type: 'summary',
      category: 'alerts',
      estimatedTime: '2-3 minutes',
      icon: <AlertCircle className="h-5 w-5" />,
    },
  ], []);

  // Mock generated reports
  const generatedReports: GeneratedReport[] = useMemo(() => [
    {
      id: 'report_001',
      name: 'Energy Consumption Summary - July 2024',
      templateName: 'Energy Consumption Summary',
      generatedAt: '2024-08-09T14:30:00Z',
      status: 'completed',
      downloadUrl: '/reports/energy-summary-july-2024.pdf',
      size: '2.4 MB',
      format: 'pdf',
    },
    {
      id: 'report_002',
      name: 'Device Efficiency Analysis - Q2 2024',
      templateName: 'Device Efficiency Analysis',
      generatedAt: '2024-08-08T09:15:00Z',
      status: 'completed',
      downloadUrl: '/reports/efficiency-analysis-q2-2024.xlsx',
      size: '1.8 MB',
      format: 'excel',
    },
    {
      id: 'report_003',
      name: 'Cost Analysis - Current Month',
      templateName: 'Cost Analysis Report',
      generatedAt: '2024-08-10T08:00:00Z',
      status: 'generating',
      format: 'pdf',
    },
  ], []);

  const datePresets = [
    { value: 'today', label: 'Today' },
    { value: 'yesterday', label: 'Yesterday' },
    { value: 'last-7-days', label: 'Last 7 Days' },
    { value: 'last-30-days', label: 'Last 30 Days' },
    { value: 'this-month', label: 'This Month' },
    { value: 'last-month', label: 'Last Month' },
    { value: 'this-quarter', label: 'This Quarter' },
    { value: 'last-quarter', label: 'Last Quarter' },
    { value: 'this-year', label: 'This Year' },
    { value: 'custom', label: 'Custom Range' },
  ];

  const formatOptions = [
    { value: 'pdf', label: 'PDF Document', icon: <FileText className="h-4 w-4" /> },
    { value: 'excel', label: 'Excel Spreadsheet', icon: <BarChart3 className="h-4 w-4" /> },
    { value: 'csv', label: 'CSV Data', icon: <Download className="h-4 w-4" /> },
    { value: 'json', label: 'JSON Data', icon: <Settings className="h-4 w-4" /> },
  ];

  const selectedTemplateData = reportTemplates.find(t => t.id === selectedTemplate);

  const handleGenerateReport = async () => {
    if (!selectedTemplate) {
      alert('Please select a report template');
      return;
    }

    setIsGenerating(true);
    
    // Simulate report generation
    try {
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Create download link simulation
      const reportData = {
        template: selectedTemplateData,
        config: reportConfig,
        generatedAt: new Date().toISOString(),
      };
      
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedTemplateData?.name.replace(/\s+/g, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.${reportConfig.format}`;
      a.click();
      URL.revokeObjectURL(url);
      
      alert('Report generated successfully!');
    } catch (error) {
      alert('Failed to generate report. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId);
    setReportConfig(prev => ({ ...prev, templateId }));
  };

  const handleDateRangeChange = (field: string, value: string) => {
    setReportConfig(prev => ({
      ...prev,
      dateRange: { ...prev.dateRange, [field]: value }
    }));
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'energy': return 'text-blue-600 bg-blue-100';
      case 'efficiency': return 'text-green-600 bg-green-100';
      case 'cost': return 'text-yellow-600 bg-yellow-100';
      case 'devices': return 'text-purple-600 bg-purple-100';
      case 'alerts': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'generating':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Energy Reports</h3>
        </div>
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-1 px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors">
            <Mail className="h-4 w-4" />
            <span>Schedule</span>
          </button>
          <button className="flex items-center space-x-1 px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors">
            <Printer className="h-4 w-4" />
            <span>Print</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'generate', label: 'Generate Report', icon: <Play className="h-4 w-4" /> },
            { id: 'history', label: 'Report History', icon: <Clock className="h-4 w-4" /> },
            { id: 'scheduled', label: 'Scheduled Reports', icon: <Calendar className="h-4 w-4" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Generate Report Tab */}
      {activeTab === 'generate' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Template Selection */}
          <div className="lg:col-span-2 space-y-4">
            <h4 className="text-md font-medium text-gray-900">Select Report Template</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reportTemplates.map((template) => (
                <div
                  key={template.id}
                  onClick={() => handleTemplateSelect(template.id)}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedTemplate === template.id
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-lg ${getCategoryColor(template.category)}`}>
                      {template.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h5 className="text-sm font-medium text-gray-900 truncate">
                        {template.name}
                      </h5>
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {template.description}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium capitalize ${getCategoryColor(template.category)}`}>
                          {template.category}
                        </span>
                        <span className="text-xs text-gray-400">
                          ~{template.estimatedTime}
                        </span>
                      </div>
                      {template.lastGenerated && (
                        <p className="text-xs text-gray-400 mt-1">
                          Last: {formatDate(template.lastGenerated)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Configuration Panel */}
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="text-md font-medium text-gray-900 mb-4">Report Configuration</h4>

              {/* Date Range */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">Date Range</label>
                <select
                  value={reportConfig.dateRange.preset}
                  onChange={(e) => handleDateRangeChange('preset', e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {datePresets.map(preset => (
                    <option key={preset.value} value={preset.value}>
                      {preset.label}
                    </option>
                  ))}
                </select>

                {reportConfig.dateRange.preset === 'custom' && (
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="date"
                      value={reportConfig.dateRange.start}
                      onChange={(e) => handleDateRangeChange('start', e.target.value)}
                      className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                      type="date"
                      value={reportConfig.dateRange.end}
                      onChange={(e) => handleDateRangeChange('end', e.target.value)}
                      className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
              </div>

              {/* Format Selection */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">Export Format</label>
                <div className="grid grid-cols-2 gap-2">
                  {formatOptions.map(format => (
                    <button
                      key={format.value}
                      onClick={() => setReportConfig(prev => ({ ...prev, format: format.value as any }))}
                      className={`flex items-center space-x-2 p-2 border rounded-md text-sm transition-colors ${
                        reportConfig.format === format.value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {format.icon}
                      <span>{format.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Content Options */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">Include</label>
                <div className="space-y-2">
                  {[
                    { key: 'includeSummary', label: 'Executive Summary' },
                    { key: 'includeCharts', label: 'Charts & Visualizations' },
                    { key: 'includeDetails', label: 'Detailed Data Tables' },
                  ].map(option => (
                    <label key={option.key} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={reportConfig[option.key as keyof ReportConfig] as boolean}
                        onChange={(e) => setReportConfig(prev => ({ 
                          ...prev, 
                          [option.key]: e.target.checked 
                        }))}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerateReport}
                disabled={!selectedTemplate || isGenerating}
                className={`w-full mt-6 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                  !selectedTemplate || isGenerating
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {isGenerating ? (
                  <div className="flex items-center justify-center space-x-2">
                    <Clock className="h-4 w-4 animate-spin" />
                    <span>Generating...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-2">
                    <Play className="h-4 w-4" />
                    <span>Generate Report</span>
                  </div>
                )}
              </button>

              {selectedTemplateData && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    {selectedTemplateData.icon}
                    <span className="text-sm font-medium text-blue-900">
                      {selectedTemplateData.name}
                    </span>
                  </div>
                  <p className="text-xs text-blue-700 mt-1">
                    Estimated time: {selectedTemplateData.estimatedTime}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Report History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-md font-medium text-gray-900">Recent Reports</h4>
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="all">All Reports</option>
                <option value="completed">Completed</option>
                <option value="generating">In Progress</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Report
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Generated
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {generatedReports.map((report) => (
                    <tr key={report.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {report.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {report.templateName}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(report.status)}
                          <span className={`text-sm capitalize ${
                            report.status === 'completed' ? 'text-green-700' :
                            report.status === 'generating' ? 'text-blue-700' :
                            'text-red-700'
                          }`}>
                            {report.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {formatDate(report.generatedAt)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {report.size || '--'}
                      </td>
                      <td className="px-4 py-3">
                        {report.status === 'completed' && (
                          <button className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800">
                            <Download className="h-4 w-4" />
                            <span>Download</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Scheduled Reports Tab */}
      {activeTab === 'scheduled' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-md font-medium text-gray-900">Scheduled Reports</h4>
            <button className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
              <Calendar className="h-4 w-4" />
              <span>New Schedule</span>
            </button>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              <h5 className="text-sm font-medium text-blue-900">Scheduled Reports Coming Soon</h5>
            </div>
            <p className="text-sm text-blue-700 mt-2">
              Automated report generation and distribution will be available in the next update. 
              You'll be able to schedule daily, weekly, and monthly reports with email delivery.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnergyReportsGenerator;
