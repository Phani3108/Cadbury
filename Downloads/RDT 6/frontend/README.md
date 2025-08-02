# Digital Twin Frontend

Vue.js frontend for the Digital Twin Teams Tab application.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- Digital Twin backend running on localhost:8000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## 🏗️ Architecture

### Components

- **ChatStream.vue**: Main chat interface with streaming responses
- **App.vue**: Root application component

### Features

- **Real-time streaming**: Responses stream word-by-word
- **Follow-up suggestions**: Quick action buttons for common follow-ups
- **Feedback system**: Thumbs up/down for response quality
- **Responsive design**: Works on desktop and mobile
- **Teams integration**: Ready for Microsoft Teams Tab deployment

### API Integration

The frontend communicates with the Digital Twin backend via:

- **POST /stream**: Server-Sent Events for streaming responses
- **POST /feedback**: Submit user feedback
- **GET /health**: Health check endpoint

## 🎨 Styling

- Uses Microsoft Teams design language
- Responsive layout for different screen sizes
- Smooth animations and transitions
- Accessible design with proper contrast

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_TEAMS_APP_ID=your-teams-app-id
```

### Teams Integration

To deploy as a Teams Tab:

1. Build the application: `npm run build`
2. Upload the `dist` folder to your Teams app
3. Configure the tab in Teams admin center

## 🧪 Testing

```bash
npm run lint
```

## 📱 Mobile Support

The application is fully responsive and works on:
- Desktop browsers
- Mobile browsers
- Teams mobile app

## 🚀 Deployment

### Local Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
```

### Teams Deployment
1. Build the application
2. Upload to Teams app store
3. Configure tab settings

## 🔗 Backend Integration

The frontend expects the backend to be running on `localhost:8000` with the following endpoints:

- `POST /stream` - Streaming chat responses
- `POST /feedback` - User feedback submission
- `GET /health` - Health check

## 📊 Analytics

The application tracks:
- User interactions
- Response quality feedback
- Usage patterns
- Error rates

## 🛠️ Development

### Adding New Features

1. Create new Vue components in `src/components/`
2. Update the main App.vue if needed
3. Test with the backend API
4. Deploy to Teams for testing

### Styling Guidelines

- Use Microsoft Teams color palette
- Follow Teams design patterns
- Ensure accessibility compliance
- Test on multiple screen sizes

## 📞 Support

For issues or questions:
- Check the backend logs
- Verify API connectivity
- Test with different browsers
- Contact the development team 