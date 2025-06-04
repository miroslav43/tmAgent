# Speech-to-Text Integration

## Overview
This project now includes speech-to-text functionality using the `react-speech-recognition` library and Web Speech API. Users can speak their questions instead of typing them.

## Features
- 🎤 **Microphone Button**: Located in the text input field on the AI agent page
- 🔴 **Visual Feedback**: Red border and pulsing microphone icon when recording
- 🇷🇴 **Romanian Language**: Configured for Romanian (`ro-RO`) speech recognition
- 🔄 **Real-time Transcription**: Speech is converted to text in real-time
- 🛑 **Smart Stop**: Automatically stops recording when user types manually
- ⚠️ **Error Handling**: Displays warnings for unsupported browsers

## How to Use
1. Navigate to the AI agent page (`/ai-agent`)
2. Look for the microphone icon in the text input field
3. Click the microphone to start recording (icon turns red and pulses)
4. Speak your question in Romanian
5. Click the microphone again to stop recording, or start typing to auto-stop
6. The transcribed text appears in the input field
7. Press Enter or click Send to submit your question

## Browser Compatibility
- ✅ **Chrome/Chromium**: Best experience with full support
- ✅ **Edge**: Good support (Chromium-based)
- ⚠️ **Firefox**: Limited support, may not work consistently
- ❌ **Safari**: Minimal support
- ❌ **Internet Explorer**: Not supported

## Technical Implementation

### Custom Hook
The `useSpeechRecognitionHook` provides:
- Browser compatibility checking
- Speech recognition state management
- Error handling
- Romanian language configuration

### Key Components
1. **Microphone Button**: Toggles recording on/off
2. **Visual Indicators**: 
   - Red border when listening
   - Pulsing red microphone icon
   - Placeholder text changes
3. **Smart Integration**: 
   - Auto-stops when typing manually
   - Clears transcript on message send
   - Handles errors gracefully

### Configuration
```typescript
SpeechRecognition.startListening({
  continuous: true,        // Keep listening until stopped
  language: 'ro-RO',      // Romanian language
  interimResults: false   // Only final results
});
```

## Error Handling
- Browser compatibility warnings
- Network connectivity issues
- Microphone permission errors
- Speech recognition service unavailability

## Privacy & Security
- Uses browser's native Web Speech API
- Speech data may be processed by Google (Chrome) or Microsoft (Edge)
- No speech data is stored locally by this application
- Users are informed about browser requirements

## Future Enhancements
- [ ] Add support for multiple languages
- [ ] Implement offline speech recognition
- [ ] Add voice activity detection
- [ ] Include confidence scoring
- [ ] Support for speech commands (e.g., "send message")

## Troubleshooting

### Microphone Not Working
1. Check browser permissions for microphone access
2. Ensure microphone is not used by other applications
3. Try refreshing the page
4. Use Chrome for best compatibility

### Poor Recognition Accuracy
1. Speak clearly and at moderate pace
2. Ensure quiet environment
3. Check microphone quality
4. Try switching to Chrome browser

### Button Not Visible
- Browser may not support speech recognition
- Check console for error messages
- Only supported browsers show the microphone button 