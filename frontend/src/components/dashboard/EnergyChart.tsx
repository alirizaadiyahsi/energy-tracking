import React from 'react';
import { Line } from 'react-chartjs-2';

const EnergyChart: React.FC<{ data: any; options?: any }> = ({ data, options }) => (
  <div className="bg-white rounded shadow p-4">
    <h3 className="font-semibold mb-2">Energy Consumption</h3>
    <Line data={data} options={options} />
  </div>
);

export default EnergyChart;
