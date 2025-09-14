import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Upload, 
  FileText, 
  Trash2, 
  Edit, 
  Download, 
  Search, 
  Plus, 
  Settings, 
  Shield, 
  GraduationCap,
  ArrowLeft,
  Eye,
  Calendar,
  User,
  Filter,
  LogOut,
  Play,
  Database,
  RefreshCw,
  FolderOpen,
  Layers
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ThemeToggle } from '@/components/ThemeToggle';
import Login from '@/components/Login';
import { toast } from 'sonner';

interface Document {
  id: string;
  filename: string;
  path: string;
  size: number;
  last_modified: string;
  status?: 'processed' | 'unprocessed';
  description?: string;
}

interface ProcessedDocument {
  content: string;
  metadata: {
    source: string;
  };
  length: number;
}

interface EnvStatus {
  GROQ_API_KEY: string;
  TOP_K: string;
  EMBED_MODEL_ID: string;
  GEN_MODEL_ID: string;
  env_file_exists: boolean;
}

interface ProcessingStatus {
  status: string;
  processed_files: number;
  total_files: number;
}

interface Base {
  name: string;
  description: string;
  documents_dir: string;
  faiss_index_path: string;
  output_docs_file: string;
}

interface BaseConfig {
  base_name: string;
  documents_dir: string;
  faiss_index_path: string;
  output_docs_file: string;
  description?: string;
}

const API_BASE_URL = import.meta.env.VITE_RAG_API_URL;
const API_KEY = import.meta.env.VITE_RAG_API_KEY;

export default function Admin() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [processedDocuments, setProcessedDocuments] = useState<ProcessedDocument[]>([]);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [envStatus, setEnvStatus] = useState<EnvStatus | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCreatingVectorStore, setIsCreatingVectorStore] = useState(false);
  const [availableBases, setAvailableBases] = useState<Base[]>([]);
  const [selectedBase, setSelectedBase] = useState<string>('default');
  const [isCreatingBase, setIsCreatingBase] = useState(false);
  const [newBaseConfig, setNewBaseConfig] = useState<BaseConfig>({
    base_name: '',
    documents_dir: '',
    faiss_index_path: '',
    output_docs_file: '',
    description: ''
  });
  const [isSwitchingBase, setIsSwitchingBase] = useState(false);

  useEffect(() => {
    const authStatus = localStorage.getItem('isAuthenticated') === 'true';
    setIsAuthenticated(authStatus);
    setIsLoading(false);

    if (authStatus) {
      fetchBases();
      fetchDocuments();
      fetchProcessedDocuments();
      fetchEnvStatus();
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && selectedBase) {
      fetchDocuments();
      fetchProcessedDocuments();
    }
  }, [selectedBase, isAuthenticated]);

  const fetchBases = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/bases/`, {
        headers: {
          'x-api-key': API_KEY,
          'accept': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const bases = Object.entries(data.bases_config || {}).map(([name, config]: [string, any]) => ({
          name,
          description: config.description || name,
          documents_dir: config.documents_dir,
          faiss_index_path: config.faiss_index_path,
          output_docs_file: config.output_docs_file
        }));
        setAvailableBases(bases);
        
        if (bases.length > 0 && !selectedBase) {
          setSelectedBase(bases[0].name);
        }
      }
    } catch (error) {
      console.error('Erro ao carregar bases:', error);
      // Fallback para bases padrão
      setAvailableBases([
        {
          name: 'default',
          description: 'Base padrão',
          documents_dir: 'documents',
          faiss_index_path: 'faiss_index',
          output_docs_file: 'processed_docs.pkl'
        }
      ]);
    }
  };

  const fetchDocuments = async () => {
    if (!selectedBase) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/`, {
        headers: {
          'x-api-key': API_KEY,
          'accept': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      } else {
        toast.error('Erro ao carregar documentos');
      }
    } catch (error) {
      toast.error('Falha na conexão com o servidor');
    }
  };

  const fetchProcessedDocuments = async () => {
    if (!selectedBase) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/processed-documents/`, {
        headers: {
          'x-api-key': API_KEY,
          'accept': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProcessedDocuments(data);
      }
    } catch (error) {
      console.error('Erro ao carregar documentos processados:', error);
    }
  };

  const isDocumentProcessed = (filename: string) => {
    return processedDocuments.some(doc => 
      doc.metadata.source.includes(filename)
    );
  };

  const getProcessedDocInfo = (filename: string) => {
    const docs = processedDocuments.filter(doc => 
      doc.metadata.source.includes(filename)
    );
    return {
      chunks: docs.length,
      totalLength: docs.reduce((total, doc) => total + doc.length, 0)
    };
  };

  const fetchEnvStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/env-status`, {
        headers: {
          'x-api-key': API_KEY,
          'accept': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setEnvStatus(data);
      }
    } catch (error) {
      console.error('Erro ao carregar status do ambiente:', error);
    }
  };

  const checkProcessingStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/status/`, {
        headers: {
          'x-api-key': API_KEY,
          'accept': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProcessingStatus(data);
        
        if (data.status === 'processing') {
          setTimeout(checkProcessingStatus, 2000);
        } else if (data.status === 'completed') {
          setIsProcessing(false);
          fetchProcessedDocuments();
          toast.success('Processamento concluído!');
        }
      }
    } catch (error) {
      console.error('Erro ao verificar status:', error);
      setIsProcessing(false);
    }
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
    fetchBases();
    fetchDocuments();
    fetchProcessedDocuments();
    fetchEnvStatus();
  };

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    setIsAuthenticated(false);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('file', file);
      });

      const response = await fetch(`${API_BASE_URL}/api/documents/`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'accept': 'application/json',
        },
        body: formData
      });

      if (response.ok) {
        toast.success('Arquivo(s) enviado(s) com sucesso!');
        fetchDocuments();
      } else {
        toast.error('Erro ao enviar arquivo(s)');
      }
    } catch (error) {
      toast.error('Falha no upload');
    } finally {
      setIsUploading(false);
    }
  };

  const deleteDocument = async (filename: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
        headers: {
          'x-api-key': API_KEY,
        }
      });

      if (response.ok) {
        toast.success('Documento deletado com sucesso!');
        fetchDocuments();
      } else {
        toast.error('Erro ao deletar documento');
      }
    } catch (error) {
      toast.error('Falha ao deletar documento');
    }
  };

  const processDocuments = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/process/`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'accept': 'application/json',
        }
      });

      if (response.ok) {
        toast.success('Processamento iniciado!');
        setTimeout(checkProcessingStatus, 1000);
      } else {
        toast.error('Erro ao iniciar processamento');
        setIsProcessing(false);
      }
    } catch (error) {
      toast.error('Falha ao iniciar processamento');
      setIsProcessing(false);
    }
  };

  const createVectorStore = async () => {
    setIsCreatingVectorStore(true);
    try {
      const response = await fetch(`${API_BASE_URL}/create-vector-store`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'Content-Type': 'application/json',
          'accept': 'application/json',
        }
      });

      if (response.ok) {
        toast.success('Vector Store criado com sucesso!');
      } else {
        toast.error('Erro ao criar Vector Store');
      }
    } catch (error) {
      toast.error('Falha ao criar Vector Store');
    } finally {
      setIsCreatingVectorStore(false);
    }
  };

  const createNewBase = async () => {
    setIsCreatingBase(true);
    try {
      const response = await fetch(`${API_BASE_URL}/bases/`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'Content-Type': 'application/json',
          'accept': 'application/json',
        },
        body: JSON.stringify(newBaseConfig)
      });

      if (response.ok) {
        toast.success('Base criada com sucesso!');
        setNewBaseConfig({
          base_name: '',
          documents_dir: '',
          faiss_index_path: '',
          output_docs_file: '',
          description: ''
        });
        fetchBases();
      } else {
        toast.error('Erro ao criar base');
      }
    } catch (error) {
      toast.error('Falha ao criar base');
    } finally {
      setIsCreatingBase(false);
    }
  };

  const deleteBase = async (baseName: string) => {
    if (baseName === 'default') {
      toast.error('Não é possível deletar a base padrão');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/bases/${baseName}`, {
        method: 'DELETE',
        headers: {
          'x-api-key': API_KEY,
        }
      });

      if (response.ok) {
        toast.success('Base deletada com sucesso!');
        fetchBases();
      } else {
        toast.error('Erro ao deletar base');
      }
    } catch (error) {
      toast.error('Falha ao deletar base');
    }
  };

  const switchBase = async (baseName: string) => {
    setIsSwitchingBase(true);
    try {
      const response = await fetch(`${API_BASE_URL}/bases/switch`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ base_name: baseName })
      });

      if (response.ok) {
        setSelectedBase(baseName);
        toast.success(`Base alterada para: ${baseName}`);
      } else {
        toast.error('Erro ao mudar de base');
      }
    } catch (error) {
      toast.error('Falha ao mudar de base');
    } finally {
      setIsSwitchingBase(false); 
    }
  };

  const updateEnvSettings = async (settings: Partial<EnvStatus>) => {
    try {
      const response = await fetch(`${API_BASE_URL}/update-env`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'Content-Type': 'application/json',
          'accept': 'application/json',
        },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        toast.success('Configurações atualizadas!');
        fetchEnvStatus();
      } else {
        toast.error('Erro ao atualizar configurações');
      }
    } catch (error) {
      toast.error('Falha ao atualizar configurações');
    }
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (doc.description || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = selectedStatus === 'all' || 
                         (selectedStatus === 'processed' && processedDocuments.some(p => p.metadata.source === doc.filename)) ||
                         (selectedStatus === 'unprocessed' && !processedDocuments.some(p => p.metadata.source === doc.filename));
    
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (filename: string) => {
    const isProcessed = isDocumentProcessed(filename);
    return isProcessed 
      ? 'bg-university-green/10 text-university-green border-university-green/20'
      : 'bg-university-gold/10 text-university-gold border-university-gold/20';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-university-blue"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-university-blue/5">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2 text-university-blue hover:text-university-blue-dark">
                <ArrowLeft className="w-5 h-5" />
                <span className="text-sm">Voltar</span>
              </Link>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-university-blue rounded-xl">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-foreground">Administração DRIACA</h1>
                  <p className="text-sm text-muted-foreground">Gerenciamento de Documentos</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="secondary" className="bg-university-blue/10 text-university-blue border-university-blue/20">
                <User className="w-3 h-3 mr-1" />
                Admin
              </Badge>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleLogout}
                className="flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Sair
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Tabs defaultValue="documents" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="documents">Documentos</TabsTrigger>
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="bases">Bases</TabsTrigger>
            <TabsTrigger value="settings">Configurações</TabsTrigger>
          </TabsList>

          {/* Documents Tab */}
          <TabsContent value="documents" className="space-y-6">
            {/* Base Selector */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  Seleção de Base
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <Select value={selectedBase} onValueChange={switchBase} disabled={isSwitchingBase}>
                      <SelectTrigger>
                        {isSwitchingBase ? (
                          <div className="flex items-center gap-2">
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <span>Alternando base...</span>
                          </div>
                        ) : (
                          <SelectValue placeholder="Selecionar base..." />
                        )}
                      </SelectTrigger>
                      <SelectContent>
                        {availableBases.map((base) => (
                          <SelectItem key={base.name} value={base.name}>
                            {base.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Badge variant="outline" className="flex items-center gap-2">
                    <FolderOpen className="w-4 h-4" />
                    {selectedBase ? availableBases.find(b => b.name === selectedBase)?.documents_dir : 'Nenhuma base selecionada'}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <Button 
                onClick={processDocuments} 
                disabled={isProcessing || documents.length === 0}
                className="flex items-center gap-2"
              >
                {isProcessing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {isProcessing ? 'Processando...' : 'Processar Documentos'}
              </Button>
              
              <Button 
                onClick={createVectorStore} 
                disabled={isCreatingVectorStore || processedDocuments.length === 0}
                className="flex items-center gap-2"
                variant="outline"
              >
                {isCreatingVectorStore ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Database className="w-4 h-4" />
                )}
                {isCreatingVectorStore ? 'Criando...' : 'Criar Vector Store'}
              </Button>

              {processingStatus && (
                <Badge variant="secondary" className="ml-auto">
                  {processingStatus.status === 'processing' 
                    ? `Processando: ${processingStatus.processed_files}/${processingStatus.total_files}`
                    : processingStatus.status
                  }
                </Badge>
              )}
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Total de Documentos</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-university-blue">{documents.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Processados</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-university-green">
                    {documents.filter(d => isDocumentProcessed(d.filename)).length}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Pendentes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-university-gold">
                    {documents.filter(d => !isDocumentProcessed(d.filename)).length}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Base Atual</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-university-blue">
                    {selectedBase}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Filters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Filter className="w-5 h-5" />
                  Filtros e Busca
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="search">Buscar</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        id="search"
                        placeholder="Nome do arquivo..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10" 
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="status">Status</Label>
                    <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                      <SelectTrigger>
                        <SelectValue placeholder="Todos os status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos os status</SelectItem>
                        <SelectItem value="processed">Processados</SelectItem>
                        <SelectItem value="unprocessed">Não Processados</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Documents List */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    Documentos ({filteredDocuments.length})
                  </span>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={fetchDocuments}
                    className="flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Atualizar
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredDocuments.map((doc) => {
                    const isProcessed = isDocumentProcessed(doc.filename);
                    const processedInfo = isProcessed ? getProcessedDocInfo(doc.filename) : null;
                    
                    return (
                      <div key={doc.filename} className="border rounded-lg p-4 hover:bg-muted/50 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <FileText className="w-5 h-5 text-university-blue" />
                              <h3 className="font-semibold">
                                {doc.filename.length > 90 
                                  ? `${doc.filename.substring(0, 90)}...` 
                                  : doc.filename
                                }
                              </h3>
                              <Badge className={getStatusColor(doc.filename)}>
                                {isProcessed ? 'Processado' : 'Não Processado'}
                              </Badge>
                            </div>
                            {isProcessed && processedInfo && (
                              <p className="text-sm text-muted-foreground mb-2">
                                Total de caracteres: {processedInfo.totalLength}
                              </p>
                            )}
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                Modificado: {new Date(doc.last_modified).toLocaleDateString('pt-BR')}
                              </span>
                              <span>Tamanho: {formatFileSize(doc.size)}</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button size="sm" variant="outline">
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="outline">
                              <Download className="w-4 h-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => deleteDocument(doc.filename)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  
                  {filteredDocuments.length === 0 && (
                    <div className="text-center py-12">
                      <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-semibold mb-2">Nenhum documento encontrado</h3>
                      <p className="text-muted-foreground">Tente ajustar os filtros ou adicione novos documentos.</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload de Documentos
                </CardTitle>
                <CardDescription>
                  Adicione novos documentos ao sistema RAG da universidade
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Base Selector */}
                <div>
                  <Label>Base de Destino</Label>
                  <Select value={selectedBase} onValueChange={switchBase} disabled={isSwitchingBase}>
                    <SelectTrigger>
                      {isSwitchingBase ? (
                        <div className="flex items-center gap-2">
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Alternando base...</span>
                        </div>
                      ) : (
                        <SelectValue placeholder="Selecionar base..." />
                      )}
                    </SelectTrigger>
                    <SelectContent>
                      {availableBases.map((base) => (
                        <SelectItem key={base.name} value={base.name}>
                          {base.description}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Upload Area */}
                <div className="border-2 border-dashed border-university-blue/30 rounded-lg p-8 text-center hover:border-university-blue/50 transition-colors">
                  <Upload className="w-12 h-12 text-university-blue mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Arraste arquivos aqui</h3>
                  <p className="text-muted-foreground mb-4">ou clique para selecionar</p>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                  />
                  <Button asChild disabled={isUploading}>
                    <label htmlFor="file-upload" className="cursor-pointer">
                      {isUploading ? 'Enviando...' : 'Selecionar Arquivos'}
                    </label>
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    Formatos aceitos: PDF, DOC, DOCX, TXT
                  </p>
                </div>

                {/* Upload Form */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="doc-description">Descrição</Label>
                      <Textarea
                        id="doc-description"
                        placeholder="Descreva o conteúdo do documento..."
                        className="resize-none"
                        rows={4}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Bases Tab */}
          <TabsContent value="bases" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Layers className="w-5 h-5" />
                  Gerenciamento de Bases
                </CardTitle>
                <CardDescription>
                  Crie e gerencie diferentes bases de conhecimento
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Create New Base */}
                <div className="border rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4">Criar Nova Base</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="base-name">Nome da Base*</Label>
                      <Input
                        id="base-name"
                        value={newBaseConfig.base_name}
                        onChange={(e) => setNewBaseConfig({...newBaseConfig, base_name: e.target.value})}
                        placeholder="ex: base_academica"
                      />
                    </div>
                    <div>
                      <Label htmlFor="base-description">Descrição</Label>
                      <Input
                        id="base-description"
                        value={newBaseConfig.description || ''}
                        onChange={(e) => setNewBaseConfig({...newBaseConfig, description: e.target.value})}
                        placeholder="Descrição da base"
                      />
                    </div>
                    <div>
                      <Label htmlFor="base-documents-dir">Diretório de Documentos*</Label>
                      <Input
                        id="base-documents-dir"
                        value={newBaseConfig.documents_dir}
                        onChange={(e) => setNewBaseConfig({...newBaseConfig, documents_dir: e.target.value})}
                        placeholder="ex: bases/academica/documents"
                      />
                    </div>
                    <div>
                      <Label htmlFor="base-faiss-path">Caminho do Índice FAISS*</Label>
                      <Input
                        id="base-faiss-path"
                        value={newBaseConfig.faiss_index_path}
                        onChange={(e) => setNewBaseConfig({...newBaseConfig, faiss_index_path: e.target.value})}
                        placeholder="ex: bases/academica/faiss_index"
                      />
                    </div>
                    <div>
                      <Label htmlFor="base-output-file">Arquivo de Saída*</Label>
                      <Input
                        id="base-output-file"
                        value={newBaseConfig.output_docs_file}
                        onChange={(e) => setNewBaseConfig({...newBaseConfig, output_docs_file: e.target.value})}
                        placeholder="ex: bases/academica/processed_docs.pkl"
                      />
                    </div>
                  </div>
                  <Button 
                    onClick={createNewBase} 
                    disabled={isCreatingBase || !newBaseConfig.base_name || !newBaseConfig.documents_dir || !newBaseConfig.faiss_index_path || !newBaseConfig.output_docs_file}
                    className="mt-4"
                  >
                    {isCreatingBase ? 'Criando...' : 'Criar Base'}
                  </Button>
                </div>

                {/* Existing Bases */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Bases Existentes</h3>
                  <div className="space-y-4">
                    {availableBases.map((base) => (
                      <div key={base.name} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold">{base.description}</h4>
                            <p className="text-sm text-muted-foreground">Nome: {base.name}</p>
                            <div className="text-xs text-muted-foreground mt-2">
                              <p>Documentos: {base.documents_dir}</p>
                              <p>Índice: {base.faiss_index_path}</p>
                              <p>Arquivo processado: {base.output_docs_file}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => switchBase(base.name)}
                              disabled={selectedBase === base.name}
                            >
                              {selectedBase === base.name ? 'Selecionada' : 'Selecionar'}
                            </Button>
                            {base.name !== 'default' && (
                              <Button 
                                size="sm" 
                                variant="destructive"
                                onClick={() => deleteBase(base.name)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Configurações do Sistema RAG
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Processamento</h3>
                    <div>
                      <Label htmlFor="chunk-size">Tamanho do Chunk</Label>
                      <Input 
                        id="chunk-size" 
                        defaultValue="1000" 
                        type="number" 
                        onChange={(e) => updateEnvSettings({ TOP_K: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Número de caracteres por fragmento de texto
                      </p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Modelos</h3>
                    <div>
                      <Label htmlFor="embed-model">Modelo de Embedding</Label>
                      <Input 
                        id="embed-model" 
                        defaultValue={envStatus?.EMBED_MODEL_ID || ''}
                        onChange={(e) => updateEnvSettings({ EMBED_MODEL_ID: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Modelo responsável por criar o banco de dados vetorial
                      </p>
                    </div>
                    <div>
                      <Label htmlFor="gen-model">Modelo de Geração</Label>
                      <Input 
                        id="gen-model" 
                        defaultValue={envStatus?.GEN_MODEL_ID || ''}
                        onChange={(e) => updateEnvSettings({ GEN_MODEL_ID: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Modelo LLM para geração de respostas
                      </p>
                    </div>
                  </div>
                </div>
                
                {envStatus && (
                  <div className="pt-6 border-t">
                    <h3 className="text-lg font-semibold mb-4">Status do Ambiente</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">GROQ_API_KEY:</span>{' '}
                        {envStatus.GROQ_API_KEY === '***' ? 'Configurada' : 'Não configurada'}
                      </div>
                      <div>
                        <span className="font-medium">Arquivo .env:</span>{' '}
                        {envStatus.env_file_exists ? 'Presente' : 'Ausente'}
                      </div>
                      <div>
                        <span className="font-medium">TOP_K:</span> {envStatus.TOP_K}
                      </div>
                      <div>
                        <span className="font-medium">Embed Model:</span> {envStatus.EMBED_MODEL_ID}
                      </div>
                      <div>
                        <span className="font-medium">Gen Model:</span> {envStatus.GEN_MODEL_ID}
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="pt-6 border-t">
                  <Button 
                    className="bg-university-blue hover:bg-university-blue-dark"
                    onClick={() => fetchEnvStatus()}
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Atualizar Status
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}