# Energy Tracking Frontend

A React + Vite frontend application for the Energy Tracking System.

## Features

- **Modern React Application**: Built with React 18 and TypeScript
- **Fast Development**: Powered by Vite for instant hot module replacement
- **Authentication**: Secure login with JWT tokens
- **Responsive Design**: Built with Tailwind CSS for all screen sizes
- **Real-time Updates**: WebSocket integration for live data
- **State Management**: React Query for server state management
- **Form Validation**: React Hook Form with Zod validation
- **Icon Library**: Lucide React icons

## Technologies Used

- **React 18** - Frontend framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **React Query** - Data fetching and caching
- **React Hook Form** - Form management
- **Zod** - Schema validation
- **Axios** - HTTP client
- **Lucide React** - Icons
- **Date-fns** - Date utilities

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env.local
   ```

3. Update environment variables in `.env.local` if needed.

4. Start the development server:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:3000`.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm test` - Run tests

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main application layout
│   └── ProtectedRoute.tsx # Route protection
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication context
├── pages/             # Page components
│   ├── Dashboard.tsx  # Dashboard page
│   ├── Devices.tsx    # Device management
│   ├── Analytics.tsx  # Analytics page
│   ├── Settings.tsx   # Settings page
│   └── Login.tsx      # Login page
├── services/          # API services
│   ├── api.ts         # Axios configuration
│   ├── authService.ts # Authentication API
│   ├── deviceService.ts # Device management API
│   └── dashboardService.ts # Dashboard API
├── types/             # TypeScript type definitions
│   └── index.ts       # Common types
├── utils/             # Utility functions
│   └── index.ts       # Common utilities
├── App.tsx            # Main application component
├── main.tsx           # Application entry point
└── index.css          # Global styles
```

## Environment Variables

- `REACT_APP_API_URL` - Backend API URL (default: http://localhost:8000)
- `REACT_APP_AUTH_URL` - Authentication service URL (default: http://localhost:8005)
- `REACT_APP_WS_URL` - WebSocket URL (default: ws://localhost:8000/ws)
- `REACT_APP_ENV` - Environment (development/production)

## Docker

### Development
```bash
docker build -f Dockerfile.dev -t energy-frontend:dev .
docker run -p 3000:3000 -v $(pwd):/app -v /app/node_modules energy-frontend:dev
```

### Production
```bash
docker build -t energy-frontend:prod .
docker run -p 80:80 energy-frontend:prod
```

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new components
3. Write meaningful commit messages
4. Test your changes thoroughly
5. Update documentation as needed

## License

This project is part of the Energy Tracking System.
