import { useState } from 'react';
import { MessageCircle, HelpCircle, X, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';

interface FloatingChatButtonProps {
  onChatClick: () => void;
  onQuickQuestionSelect?: (question: string) => void; 
}

export default function FloatingChatButton({ 
  onChatClick, 
  onQuickQuestionSelect 
}: FloatingChatButtonProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const quickQuestions = [
    "Quais os passos para submeter o TCC?",
    "Como desbloquear o siga?",
    "Qual o processo para envio de ACCs?",
    "Onde verificar pendências de documentos?"
  ];

  const handleQuickQuestion = (question: string) => {
    onChatClick();
    if (onQuickQuestionSelect) {
      onQuickQuestionSelect(question); 
    }
    setIsExpanded(false);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Expanded Menu */}
      {isExpanded && (
        <div className="absolute bottom-20 right-0 mb-2">
          <Card className="w-80 shadow-2xl border-university-blue/20 bg-background/95 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-5 h-5 text-university-blue" />
                  <span className="font-semibold text-sm">Perguntas Rápidas</span>
                </div>
                <Badge variant="secondary" className="text-xs bg-university-green/10 text-university-green">
                  FAQ
                </Badge>
              </div>
              
              <div className="space-y-2 mb-4">
                {quickQuestions.map((question, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    size="sm"
                    onClick={() => handleQuickQuestion(question)}
                    className="w-full justify-start text-left h-auto py-2 px-3 hover:bg-university-blue/10 hover:text-university-blue"
                  >
                    <span className="text-xs leading-relaxed">{question}</span>
                  </Button>
                ))}
              </div>
              
              <Button
                onClick={() => {
                  onChatClick();
                  setIsExpanded(false);
                }}
                className="w-full bg-university-blue hover:bg-university-blue-dark text-white"
                size="sm"
              >
                <MessageCircle className="w-4 h-4 mr-2" />
                Abrir Chat Completo
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Floating Button */}
      <Button
        size="lg"
        onClick={() => setIsExpanded(!isExpanded)}
        className={`
          w-16 h-16 rounded-full shadow-2xl transition-all duration-300 transform hover:scale-110
          ${isExpanded 
            ? 'bg-university-navy hover:bg-university-navy/90 rotate-45' 
            : 'bg-gradient-to-r from-university-blue to-university-blue-dark hover:from-university-blue-dark hover:to-university-navy'
          }
          text-white border-2 border-white/20
        `}
      >
        {isExpanded ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageCircle className="w-6 h-6" />
        )}
      </Button>

    </div>
  );
}
