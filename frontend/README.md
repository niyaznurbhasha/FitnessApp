# Fitness App - React Native Frontend

A React Native app built with Expo that can run on web, iOS, and Android.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Expo CLI: `npm install -g @expo/cli`

### Development
```bash
cd frontend
npm install
npm start
```

### Platforms
- **Web**: `npm run web` or press `w` in terminal
- **iOS**: `npm run ios` or press `i` in terminal (requires Xcode)
- **Android**: `npm run android` or press `a` in terminal (requires Android Studio)

## 📱 Features

- **Chat Interface**: Natural language nutrition logging
- **Quick Actions**: Pre-defined meal examples
- **Conversation History**: See your chat history
- **Cross-Platform**: Works on web, iOS, and Android
- **Real-time**: Instant responses from AI

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```
EXPO_PUBLIC_API_BASE=https://your-staging-api-url.onrender.com
```

### API Integration
The app connects to the FastAPI backend for:
- Chat processing (`/chat`)
- Meal logging (`/meals/quick-log`)
- Daily summaries (`/meals/daily-summary`)
- Health checks (`/health`)

## 📦 Building for Production

### Web (Vercel)
```bash
npm run build:web
```

### iOS
```bash
npx eas build --platform ios
```

### Android
```bash
npx eas build --platform android
```

## 🎯 iOS Development Workflow

1. **Develop**: Use Expo Go app on your iPhone for testing
2. **Test**: Run on iOS Simulator for development
3. **Build**: Use EAS Build for production builds
4. **Deploy**: Submit to App Store Connect

## 🔄 Deployment

- **Web**: Auto-deploys to Vercel on push to main
- **Mobile**: Manual builds via EAS Build
- **CI/CD**: GitHub Actions runs tests on every push

## 📱 Mobile App Features

- Native iOS/Android performance
- Push notifications (future)
- Offline support (future)
- Camera integration for food photos (future)
- Biometric authentication (future)
