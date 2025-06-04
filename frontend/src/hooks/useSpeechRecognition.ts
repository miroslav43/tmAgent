import { useEffect, useState } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

interface UseSpeechRecognitionReturn {
  transcript: string;
  isListening: boolean;
  hasRecognitionSupport: boolean;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
  error: string | null;
}

export const useSpeechRecognitionHook = (): UseSpeechRecognitionReturn => {
  const [error, setError] = useState<string | null>(null);
  
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  const hasRecognitionSupport = browserSupportsSpeechRecognition;

  const startListening = () => {
    if (!hasRecognitionSupport) {
      setError('Browser does not support speech recognition');
      return;
    }
    
    setError(null);
    SpeechRecognition.startListening({
      continuous: true,
      language: 'ro-RO', // Romanian language
      interimResults: false
    });
  };

  const stopListening = () => {
    SpeechRecognition.stopListening();
  };

  useEffect(() => {
    if (!hasRecognitionSupport) {
      setError('Speech recognition is not supported in this browser. Please use Chrome for the best experience.');
    }
  }, [hasRecognitionSupport]);

  return {
    transcript,
    isListening: listening,
    hasRecognitionSupport,
    startListening,
    stopListening,
    resetTranscript,
    error
  };
}; 