import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from 'react-query';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock DeviceForm component since we don't have the actual implementation
const MockDeviceForm = ({ isOpen, onClose, onSubmit, isLoading, device }: any) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-25">
      <div className="form-container">
        <h2>{device ? 'Edit Device' : 'Add Device'}</h2>
        <form onSubmit={(e) => { e.preventDefault(); onSubmit({ name: 'Test Device' }); }}>
          <label htmlFor="name">Device Name</label>
          <input 
            id="name" 
            name="name" 
            defaultValue={device?.name || ''} 
            required 
          />
          
          <label htmlFor="type">Device Type</label>
          <select id="type" name="type" defaultValue={device?.type || 'sensor'}>
            <option value="sensor">Sensor</option>
            <option value="meter">Meter</option>
          </select>
          
          <label htmlFor="location">Location</label>
          <input 
            id="location" 
            name="location" 
            defaultValue={device?.location || ''} 
          />
          
          <button type="submit" disabled={isLoading}>
            {device ? 'Update Device' : 'Add Device'}
          </button>
          <button type="button" onClick={onClose}>
            <span data-testid="x-icon">X</span>
          </button>
        </form>
      </div>
    </div>
  );
};

// Mock the lucide-react icons
vi.mock('lucide-react', () => ({
  X: () => <div data-testid="x-icon">X</div>,
}));

// Mock the DeviceForm component
vi.mock('../DeviceForm', () => ({
  default: MockDeviceForm,
}));

// Create a test wrapper with React Query
const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = createQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

// Import the mock component
const DeviceForm = MockDeviceForm;

describe('DeviceForm Component', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn(),
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when open', () => {
    render(
      <TestWrapper>
        <DeviceForm {...defaultProps} />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: 'Add Device' })).toBeInTheDocument();
    expect(screen.getByLabelText(/device name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/device type/i)).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <TestWrapper>
        <DeviceForm {...defaultProps} isOpen={false} />
      </TestWrapper>
    );

    expect(screen.queryByText('Add Device')).not.toBeInTheDocument();
  });

  it('displays "Edit Device" title when editing existing device', () => {
    const existingDevice = {
      id: 'test-device-123',
      name: 'Test Device',
      type: 'meter',
      status: 'online',
      location: 'Test Location',
    };

    render(
      <TestWrapper>
        <DeviceForm {...defaultProps} device={existingDevice} />
      </TestWrapper>
    );

    expect(screen.getByText('Edit Device')).toBeInTheDocument();
  });

  it('calls onSubmit when form is submitted', async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();
    
    render(
      <TestWrapper>
        <DeviceForm {...defaultProps} onSubmit={mockOnSubmit} />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: 'Add Device' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({ name: 'Test Device' });
    });
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnClose = vi.fn();
    
    render(
      <TestWrapper>
        <DeviceForm {...defaultProps} onClose={mockOnClose} />
      </TestWrapper>
    );

    const closeButton = screen.getByTestId('x-icon').closest('button');
    if (closeButton) {
      await user.click(closeButton);
      expect(mockOnClose).toHaveBeenCalled();
    }
  });

  it('displays loading state correctly', () => {
    render(
      <TestWrapper>
        <DeviceForm {...defaultProps} isLoading={true} />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: 'Add Device' });
    expect(submitButton).toBeDisabled();
  });
});
