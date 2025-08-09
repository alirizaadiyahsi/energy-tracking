import React from 'react';

export interface TimeIntervalOption {
  value: string;
  label: string;
  interval: 'minutely' | 'hourly' | 'daily';
  timeRange: '1h' | '24h' | '7d' | '30d';
}

interface TimeIntervalSelectorProps {
  selectedInterval: TimeIntervalOption;
  onIntervalChange: (interval: TimeIntervalOption) => void;
}

const timeIntervals: TimeIntervalOption[] = [
  {
    value: 'minutely_1h',
    label: 'Last Hour (Minutely)',
    interval: 'minutely',
    timeRange: '1h'
  },
  {
    value: 'hourly_24h',
    label: 'Last 24 Hours (Hourly)',
    interval: 'hourly',
    timeRange: '24h'
  },
  {
    value: 'daily_7d',
    label: 'Last Week (Daily)',
    interval: 'daily',
    timeRange: '7d'
  },
  {
    value: 'daily_30d',
    label: 'Last Month (Daily)',
    interval: 'daily',
    timeRange: '30d'
  }
];

const TimeIntervalSelector: React.FC<TimeIntervalSelectorProps> = ({
  selectedInterval,
  onIntervalChange
}) => {
  return (
    <div className="relative">
      <label htmlFor="time-interval" className="sr-only">
        Time Interval
      </label>
      <div className="relative">
        <select
          id="time-interval"
          value={selectedInterval.value}
          onChange={(e) => {
            const interval = timeIntervals.find(ti => ti.value === e.target.value);
            if (interval) {
              console.log('Time interval changed to:', interval);
              onIntervalChange(interval);
            }
          }}
          className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm font-medium text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
        >
          {timeIntervals.map((interval) => (
            <option key={interval.value} value={interval.value}>
              {interval.label}
            </option>
          ))}
        </select>
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          <svg className="h-4 w-4 text-gray-400 fill-current" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default TimeIntervalSelector;
export { timeIntervals };
