import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BookOpen, GraduationCap, Search, Sparkles, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Badge } from './ui/badge';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  type?: 'text' | 'suggestion';
  sources?: any[];
}

interface Source {
  metadata: {
    source: string;
  };
  page_content: string;
}

interface APIResponse {
  input: string;
  resposta: string;
  contexto: Source[];
}

interface ResetResponse {
  status: string;
  message: string;
}

export function ChatBot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Olá! Sou o assistente acadêmico da universidade. Como posso ajudá-lo hoje? Posso responder dúvidas sobre pesquisa, comprovante de matricula, estagio obrigatorio, solicitação de documentos e muito mais!',
      sender: 'bot',
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [showSources, setShowSources] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const suggestedQuestions = [
    'Onde envio atestado médico ?',
    'Como solicitar comprovante de matrícula ao DRCA?',
    'Como posso cumprir as minhas horas complementares?',
    'Vocês avisam quando o diploma está pronto pra retirar?',
    'Onde submeter meus certificados para contabilizar horas de ACCs?',
    'Quais os passos para submeter o TCC?'
  ];

  const API_URL = import.meta.env.VITE_RAG_API_URL;
  const API_KEY = import.meta.env.VITE_RAG_API_KEY;

  const callRAGAPI = async (question: string): Promise<APIResponse> => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: question,
          user_id: "123",
          session_id: "abc"
        })
      });

      if (!response.ok) {
        throw new Error(`Erro na API: ${response.status}`);
      }

      const data: APIResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Erro ao chamar API:', error);
      throw error;
    }
  };

  const resetConversation = async (): Promise<ResetResponse> => {
    try {
      // A URL para resetar a conversa é a base da API + /reset-conversation
      const resetUrl = API_URL.replace('/query', '/reset-conversation');
      
      const response = await fetch(resetUrl, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Erro ao resetar conversa: ${response.status}`);
      }

      const data: ResetResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Erro ao resetar conversa:', error);
      throw error;
    }
  };

  const handleResetConversation = async () => {
    setIsResetting(true);
    try {
      // Chamar a API para resetar a conversa no backend
      await resetConversation();
      
      // Resetar o estado local da conversa
      setMessages([
        {
          id: Date.now().toString(),
          content: 'Olá! Sou o assistente acadêmico da universidade. Como posso ajudá-lo hoje? Posso responder dúvidas sobre pesquisa, comprovante de matricula, estagio obrigatorio, solicitação de documentos e muito mais!',
          sender: 'bot',
          timestamp: new Date(),
        }
      ]);
      setSources([]);
      setShowSources(false);
      
      // Mostrar mensagem de sucesso
      console.log('Conversa resetada com sucesso!');
      
    } catch (error) {
      // Em caso de erro, ainda resetar localmente mas mostrar mensagem
      setMessages([
        {
          id: Date.now().toString(),
          content: 'Olá! Sou o assistente acadêmico da universidade. Como posso ajudá-lo hoje? Posso responder dúvidas sobre pesquisa, comprovante de matricula, estagio obrigatorio, solicitação de documentos e muito mais!',
          sender: 'bot',
          timestamp: new Date(),
        }
      ]);
      setSources([]);
      setShowSources(false);
      
      console.error('Erro ao resetar conversa no servidor, mas histórico local foi limpo');
    } finally {
      setIsResetting(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await callRAGAPI(inputValue);
      
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: response.resposta,
        sender: 'bot',
        timestamp: new Date(),
        sources: response.contexto
      };

      setMessages(prev => [...prev, botResponse]);
      setSources(response.contexto || []);
      
    } catch (error) {
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Desculpe, estou com problemas técnicos no momento. Por favor, tente novamente mais tarde.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInputValue(question);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleSources = () => {
    setShowSources(!showSources);
  };

  return (
    <div className="flex flex-col h-full max-w-10x2 mx-auto bg-background border rounded-xl shadow-lg">
      {/* Header com botão de reset */}
      <div className="p-6 border-b bg-gradient-to-r from-university-blue to-university-blue-dark text-white rounded-t-xl">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-full">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Assistente Acadêmico</h2>
            <p className="text-blue-100 text-sm">Sistema RAG - DRIACA</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-university-gold" />
            <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
              Online
            </Badge>
            
            {/* Botão para resetar conversa */}
            <Button
              onClick={handleResetConversation}
              disabled={isResetting || messages.length <= 1}
              variant="destructive"
              size="sm"
              className="ml-4 bg-red-600 hover:bg-red-700 text-white"
              title="Resetar conversa"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              {isResetting ? 'Resetando...' : 'Resetar'}
            </Button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-[3] p-4 overflow-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.sender === 'bot' && (
                <div className="flex-shrink-0 w-8 h-8 bg-university-blue rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}
              
              <Card className={`max-w-[80%] p-4 ${
                message.sender === 'user' 
                  ? 'bg-chat-user border-university-blue/20' 
                  : 'bg-chat-bot border-border'
              }`}>
                <p className="text-sm leading-relaxed">{message.content}</p>
                
                {message.sender === 'bot' && message.sources && message.sources.length > 0 && (
                  <div className="mt-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={toggleSources}
                      className="text-xs flex items-center gap-1"
                    >
                      <BookOpen className="w-3 h-3" />
                      {showSources ? 'Ocultar Fontes' : 'Mostrar Fontes'}
                    </Button>
                    
                    {showSources && (
                      <div className="mt-2 p-3 rounded-md border">
                        <h4 className="text-xs font-semibold mb-2">📚 Fontes da resposta:</h4>
                        {message.sources.map((source: Source, index: number) => (
                          <div key={index} className="mb-3 last:mb-0">
                            <p className="text-xs font-medium">
                              <strong>Fonte {index + 1}:</strong> {source.metadata.source}
                            </p>
                            <div className="text-xs p-2 mt-1 rounded border overflow-auto max-h-32">
                              {source.page_content}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                
                <span className="text-xs text-muted-foreground mt-2 block">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </Card>

              {message.sender === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 bg-university-gold rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 w-8 h-8 bg-university-blue rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <Card className="max-w-[80%] p-4 bg-chat-bot border-border">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-university-blue rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-university-blue rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-university-blue rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </Card>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="p-4 border-t bg-muted/50">
          <div className="flex items-center gap-2 mb-3">
            <Search className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">Perguntas sugeridas:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => handleSuggestedQuestion(question)}
                className="text-xs hover:bg-university-blue hover:text-white transition-colors"
              >
                {question}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t bg-card">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Digite sua pergunta sobre a universidade..."
            className="flex-1 bg-chat-input border-border focus:border-university-blue"
            disabled={isTyping}
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className="bg-university-blue hover:bg-university-blue-dark text-white px-4"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Este assistente utiliza IA para fornecer informações acadêmicas. Para questões específicas, consulte o setor.
        </p>
      </div>
    </div>
  );
}