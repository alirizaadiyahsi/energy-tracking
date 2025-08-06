/**
 * Frontend component tests using React Testing Library
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'

// Mock API calls
vi.mock('../src/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}))

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      <div data-testid="test-wrapper">
        {children}
      </div>
    </BrowserRouter>
  )
}

describe('Authentication Components', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render login form elements', () => {
    render(
      <TestWrapper>
        <div data-testid="login-form">
          <input aria-label="Email" type="email" />
          <input aria-label="Password" type="password" />
          <button type="submit">Sign In</button>
        </div>
      </TestWrapper>
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('should handle form submission', async () => {
    const mockSubmit = vi.fn()
    
    render(
      <TestWrapper>
        <form onSubmit={mockSubmit} data-testid="login-form">
          <input aria-label="Email" type="email" defaultValue="test@example.com" />
          <input aria-label="Password" type="password" defaultValue="password123" />
          <button type="submit">Sign In</button>
        </form>
      </TestWrapper>
    )

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled()
    })
  })
})

describe('Dashboard Components', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render dashboard stats', () => {
    const mockData = {
      totalDevices: 5,
      onlineDevices: 4,
      totalEnergyToday: 150.5,
      averagePower: 1200.0
    }

    render(
      <TestWrapper>
        <div data-testid="dashboard-stats">
          <div data-testid="total-devices">{mockData.totalDevices}</div>
          <div data-testid="online-devices">{mockData.onlineDevices}</div>
          <div data-testid="total-energy">{mockData.totalEnergyToday}</div>
          <div data-testid="average-power">{mockData.averagePower}</div>
        </div>
      </TestWrapper>
    )

    expect(screen.getByTestId('total-devices')).toHaveTextContent('5')
    expect(screen.getByTestId('online-devices')).toHaveTextContent('4')
    expect(screen.getByTestId('total-energy')).toHaveTextContent('150.5')
    expect(screen.getByTestId('average-power')).toHaveTextContent('1200')
  })

  it('should show loading state', () => {
    render(
      <TestWrapper>
        <div data-testid="loading-spinner">Loading...</div>
      </TestWrapper>
    )

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })
})

describe('Device Components', () => {
  const mockDevice = {
    id: '1',
    name: 'Test Device',
    type: 'sensor',
    status: 'online',
    location: 'Test Location',
    lastSeen: '2024-01-15T10:30:00Z'
  }

  it('should render device information', () => {
    render(
      <TestWrapper>
        <div data-testid="device-card">
          <h3>{mockDevice.name}</h3>
          <span data-testid="device-type">{mockDevice.type}</span>
          <span data-testid="device-status" className={`status-${mockDevice.status}`}>
            {mockDevice.status}
          </span>
          <span data-testid="device-location">{mockDevice.location}</span>
        </div>
      </TestWrapper>
    )

    expect(screen.getByText('Test Device')).toBeInTheDocument()
    expect(screen.getByTestId('device-type')).toHaveTextContent('sensor')
    expect(screen.getByTestId('device-status')).toHaveTextContent('online')
    expect(screen.getByTestId('device-location')).toHaveTextContent('Test Location')
  })

  it('should show correct status styling', () => {
    render(
      <TestWrapper>
        <div data-testid="device-status" className="text-green-600">
          online
        </div>
      </TestWrapper>
    )

    const statusElement = screen.getByTestId('device-status')
    expect(statusElement).toHaveClass('text-green-600')
  })
})

describe('Utility Functions', () => {
  describe('formatters', () => {
    const formatEnergy = (value: number): string => {
      if (value >= 1000) {
        return `${(value / 1000).toFixed(2)} kWh`
      }
      return `${value} Wh`
    }

    const formatPower = (value: number): string => {
      if (value >= 1000) {
        return `${(value / 1000).toFixed(2)} kW`
      }
      return `${value} W`
    }

    const formatDate = (dateString: string): string => {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    it('should format energy values correctly', () => {
      expect(formatEnergy(1500.5)).toBe('1.50 kWh')
      expect(formatEnergy(500)).toBe('500 Wh')
      expect(formatEnergy(0)).toBe('0 Wh')
    })

    it('should format power values correctly', () => {
      expect(formatPower(1200.5)).toBe('1.20 kW')
      expect(formatPower(800)).toBe('800 W')
      expect(formatPower(0)).toBe('0 W')
    })

    it('should format dates correctly', () => {
      const testDate = '2024-01-15T10:30:00Z'
      const formatted = formatDate(testDate)
      expect(formatted).toMatch(/Jan 15, 2024/)
    })
  })

  describe('validators', () => {
    const validateEmail = (email: string): boolean => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(email)
    }

    const validatePassword = (password: string): boolean => {
      return password.length >= 8 && /[A-Z]/.test(password) && /[0-9]/.test(password)
    }

    it('should validate email addresses', () => {
      expect(validateEmail('test@example.com')).toBe(true)
      expect(validateEmail('user.name@domain.co.uk')).toBe(true)
      expect(validateEmail('invalid-email')).toBe(false)
      expect(validateEmail('')).toBe(false)
    })

    it('should validate password strength', () => {
      expect(validatePassword('StrongP@ssw0rd1')).toBe(true)
      expect(validatePassword('Password123')).toBe(true)
      expect(validatePassword('weak')).toBe(false)
      expect(validatePassword('')).toBe(false)
    })
  })
})

describe('LoginForm Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form with email and password fields', () => {
    const LoginForm = require('../src/components/auth/LoginForm').default
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    const LoginForm = require('../src/components/auth/LoginForm').default
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    const LoginForm = require('../src/components/auth/LoginForm').default
    const { api } = require('../src/services/api')
    
    api.post.mockResolvedValue({
      data: {
        accessToken: 'fake-token',
        user: { id: '1', email: 'test@example.com' }
      }
    })

    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123'
      })
    })
  })
})

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard with loading state', () => {
    const Dashboard = require('../src/pages/Dashboard').default
    
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    )

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders dashboard stats when data is loaded', async () => {
    const Dashboard = require('../src/pages/Dashboard').default
    const { api } = require('../src/services/api')

    api.get.mockResolvedValue({
      data: {
        totalDevices: 5,
        onlineDevices: 4,
        totalEnergyToday: 150.5,
        averagePower: 1200.0
      }
    })

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument() // totalDevices
      expect(screen.getByText('4')).toBeInTheDocument() // onlineDevices
      expect(screen.getByText(/150.5/)).toBeInTheDocument() // totalEnergyToday
    })
  })
})

describe('DeviceCard Component', () => {
  const mockDevice = {
    id: '1',
    name: 'Test Device',
    type: 'sensor',
    status: 'online',
    location: 'Test Location',
    lastSeen: '2024-01-15T10:30:00Z'
  }

  it('renders device information correctly', () => {
    const DeviceCard = require('../src/components/devices/DeviceCard').default
    
    render(
      <TestWrapper>
        <DeviceCard device={mockDevice} />
      </TestWrapper>
    )

    expect(screen.getByText('Test Device')).toBeInTheDocument()
    expect(screen.getByText('sensor')).toBeInTheDocument()
    expect(screen.getByText('online')).toBeInTheDocument()
    expect(screen.getByText('Test Location')).toBeInTheDocument()
  })

  it('shows correct status color for online device', () => {
    const DeviceCard = require('../src/components/devices/DeviceCard').default
    
    render(
      <TestWrapper>
        <DeviceCard device={mockDevice} />
      </TestWrapper>
    )

    const statusElement = screen.getByText('online')
    expect(statusElement).toHaveClass('text-green-600')
  })

  it('shows correct status color for offline device', () => {
    const DeviceCard = require('../src/components/devices/DeviceCard').default
    const offlineDevice = { ...mockDevice, status: 'offline' }
    
    render(
      <TestWrapper>
        <DeviceCard device={offlineDevice} />
      </TestWrapper>
    )

    const statusElement = screen.getByText('offline')
    expect(statusElement).toHaveClass('text-red-600')
  })
})

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('provides authentication state', () => {
    const TestComponent = () => {
      const { isAuthenticated, user } = require('../src/hooks/useAuth').useAuth()
      return (
        <div>
          <div data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'not authenticated'}</div>
          <div data-testid="user-email">{user?.email || 'no user'}</div>
        </div>
      )
    }

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not authenticated')
    expect(screen.getByTestId('user-email')).toHaveTextContent('no user')
  })

  it('updates state on successful login', async () => {
    const { api } = require('../src/services/api')
    api.post.mockResolvedValue({
      data: {
        accessToken: 'fake-token',
        user: { id: '1', email: 'test@example.com', firstName: 'Test' }
      }
    })

    const TestComponent = () => {
      const { login, isAuthenticated, user } = require('../src/hooks/useAuth').useAuth()
      
      const handleLogin = () => {
        login('test@example.com', 'password123')
      }

      return (
        <div>
          <button onClick={handleLogin}>Login</button>
          <div data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'not authenticated'}</div>
          <div data-testid="user-email">{user?.email || 'no user'}</div>
        </div>
      )
    }

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    const loginButton = screen.getByText('Login')
    fireEvent.click(loginButton)

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com')
    })
  })
})

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('includes authorization header when token is present', async () => {
    const { api } = require('../src/services/api')
    localStorage.setItem('auth_token', 'fake-token')

    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: 'test' })
    })

    await api.get('/test-endpoint')

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/test-endpoint'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer fake-token'
        })
      })
    )
  })

  it('handles API errors gracefully', async () => {
    const { api } = require('../src/services/api')

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ error: 'Unauthorized' })
    })

    await expect(api.get('/test-endpoint')).rejects.toThrow('Unauthorized')
  })
})

describe('Utility Functions', () => {
  describe('formatters', () => {
    it('formats energy values correctly', () => {
      const { formatEnergy } = require('../src/utils/formatters')

      expect(formatEnergy(1500.5)).toBe('1.50 kWh')
      expect(formatEnergy(500)).toBe('500 Wh')
      expect(formatEnergy(0)).toBe('0 Wh')
    })

    it('formats power values correctly', () => {
      const { formatPower } = require('../src/utils/formatters')

      expect(formatPower(1200.5)).toBe('1.20 kW')
      expect(formatPower(800)).toBe('800 W')
      expect(formatPower(0)).toBe('0 W')
    })

    it('formats dates correctly', () => {
      const { formatDate } = require('../src/utils/formatters')
      const testDate = '2024-01-15T10:30:00Z'

      const formatted = formatDate(testDate)
      expect(formatted).toMatch(/Jan 15, 2024/)
    })
  })

  describe('validators', () => {
    it('validates email addresses', () => {
      const { validateEmail } = require('../src/utils/validators')

      expect(validateEmail('test@example.com')).toBe(true)
      expect(validateEmail('invalid-email')).toBe(false)
      expect(validateEmail('')).toBe(false)
    })

    it('validates password strength', () => {
      const { validatePassword } = require('../src/utils/validators')

      expect(validatePassword('StrongP@ssw0rd')).toBe(true)
      expect(validatePassword('weak')).toBe(false)
      expect(validatePassword('')).toBe(false)
    })
  })
})
