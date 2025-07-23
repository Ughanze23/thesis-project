# ZK Audit System - Frontend

Zero-Knowledge Data Integrity Audit System frontend application built with React and TypeScript.

## Features

- **Upload Interface**: Drag-and-drop CSV file upload with real-time processing feedback
- **Audit Configuration**: Configure confidence levels and corruption detection parameters  
- **Real-time Monitoring**: Live audit progress tracking and status updates
- **Results Dashboard**: Comprehensive visualization of verification results
- **STARK Proof Visualization**: Visual representation of zero-knowledge proof execution
- **Performance Metrics**: Detailed timing and efficiency analytics

## Technology Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Heroicons** for icons
- **React Router** for navigation
- **Context API** for state management

## Getting Started

### Prerequisites

- Node.js 16.0 or higher
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Header.tsx
├── context/            # React Context providers
│   └── AuditContext.tsx
├── pages/              # Main application pages
│   ├── HomePage.tsx
│   ├── UploadPage.tsx
│   ├── AuditPage.tsx
│   └── ResultsPage.tsx
├── App.tsx            # Main application component
├── index.tsx          # Application entry point
└── App.css           # Global styles
```

## Key Components

### AuditContext
Central state management for:
- Upload tracking
- Audit configuration
- Results storage
- Loading states

### Upload Flow
1. File validation (CSV format, size limits)
2. Block generation simulation
3. Merkle tree construction
4. Cloud upload simulation
5. Metadata storage

### Audit Process
1. Dataset selection
2. Parameter configuration (confidence level, corruption rate)
3. Sample size calculation
4. Random block selection
5. STARK proof generation and verification
6. Results presentation

### Results Display
- Overall audit status
- Block-level verification results
- Performance metrics
- STARK proof analysis
- Interactive charts and visualizations

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=https://your-api-gateway-url
REACT_APP_AWS_REGION=us-east-1
```

### API Integration

The frontend is designed to integrate with:
- AWS API Gateway endpoints
- Lambda function responses
- S3 upload interfaces
- DynamoDB queries

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run test suite
- `npm run eject` - Eject from Create React App

### Adding New Features

1. Create new components in `src/components/`
2. Add new pages to `src/pages/`
3. Update routing in `App.tsx`
4. Extend context state in `AuditContext.tsx`

## Deployment

### Static Hosting (S3 + CloudFront)

1. Build the application:
```bash
npm run build
```

2. Upload `build/` contents to S3 bucket

3. Configure CloudFront distribution

### Container Deployment

```dockerfile
FROM node:16-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Security Considerations

- All sensitive cryptographic operations happen server-side
- Frontend only displays verification results
- No private keys or authentication paths exposed
- CORS properly configured for API endpoints

## Performance Optimization

- Code splitting with React.lazy()
- Memoized components with React.memo()
- Optimized bundle size with tree shaking
- CDN delivery for static assets

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow TypeScript strict mode
2. Use Tailwind CSS for styling
3. Maintain responsive design
4. Include proper error handling
5. Add loading states for async operations