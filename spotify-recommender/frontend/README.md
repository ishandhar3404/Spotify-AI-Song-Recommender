# Spotify Playlist Recommender - Frontend

A React-based frontend for the Spotify Playlist Recommender application. This frontend provides an intuitive user interface for generating personalized playlists using AI-powered recommendations.

## Features

- **Spotify OAuth Integration**: Secure authentication with Spotify accounts
- **Mood-Based Playlist Generation**: Choose from 8 different moods
- **Genre Filtering**: Optional genre-specific recommendations
- **Customizable Playlist Length**: Generate playlists with 5-50 songs
- **Seed Track Selection**: Use your favorite tracks to guide recommendations
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Real-time Playlist Generation**: Instant AI-powered recommendations

## Tech Stack

- **React 18**: Modern React with hooks and functional components
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API calls
- **Lucide React**: Beautiful icon library

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Header.jsx      # Navigation and user menu
├── contexts/           # React contexts
│   └── AuthContext.jsx # Authentication state management
├── pages/              # Page components
│   ├── Home.jsx        # Landing page
│   ├── Login.jsx       # Spotify authentication
│   ├── Dashboard.jsx   # User dashboard
│   └── PlaylistGenerator.jsx # Playlist generation interface
├── services/           # API services
│   └── api.js          # HTTP client and API endpoints
├── utils/              # Utility functions
│   └── constants.js    # Application constants
├── App.jsx             # Main application component
├── main.jsx            # Application entry point
└── index.css           # Global styles and Tailwind imports
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend server running on `http://localhost:8000`
- Spotify Developer account with OAuth credentials

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and add your Spotify credentials:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_SPOTIFY_CLIENT_ID=your_spotify_client_id_here
   VITE_SPOTIFY_REDIRECT_URI=http://localhost:3000/auth/callback
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Usage

### Authentication Flow

1. Click "Connect with Spotify" on the home page
2. Authorize the application in Spotify
3. You'll be redirected back and automatically logged in

### Generating Playlists

1. Navigate to the "Generate" page
2. Select your desired mood (Energetic, Chill, Focused, etc.)
3. Optionally choose a specific genre
4. Set playlist length (5-50 songs)
5. Optionally select a seed track from your library
6. Click "Generate Playlist"
7. Review and save your generated playlist

### Dashboard Features

- View your Spotify profile information
- See your top tracks and saved songs
- Quick access to playlist generation
- Refresh your listening data from Spotify

## API Integration

The frontend communicates with the backend through the following endpoints:

- **Authentication**: `/auth/spotify/*`
- **User Data**: `/api/user/*`
- **Playlist Generation**: `/api/playlists/*`
- **Analytics**: `/api/analytics/*`

## Styling

The application uses Tailwind CSS with custom Spotify-inspired colors:

- **Primary Green**: `#1DB954` (Spotify brand color)
- **Background**: `#191414` (Spotify dark theme)
- **Cards**: `#282828` (Spotify card background)
- **Text**: White and gray variations

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Code Style

- Use functional components with hooks
- Follow React best practices
- Use Tailwind CSS for styling
- Implement proper error handling
- Add loading states for better UX

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure backend CORS is configured for `localhost:3000`
2. **Authentication Failures**: Check Spotify OAuth credentials in `.env`
3. **API Connection**: Verify backend is running on port 8000
4. **Build Errors**: Clear `node_modules` and reinstall dependencies

### Debug Mode

Enable debug logging by setting `VITE_ENABLE_LOGGING=true` in your `.env` file.

## Contributing

1. Follow the existing code structure
2. Add proper error handling
3. Include loading states
4. Test on multiple screen sizes
5. Update documentation as needed

## License

This project is part of the Spotify Playlist Recommender application.
