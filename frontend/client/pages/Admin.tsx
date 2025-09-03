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
  LogOut
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

interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadDate: string;
  lastModified: string;
  status: 'active' | 'draft' | 'archived';
  description: string;
}

export default function Admin() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Verificar se o usuário está autenticado
    const authStatus = localStorage.getItem('isAuthenticated') === 'true';
    setIsAuthenticated(authStatus);
    setIsLoading(false);
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    setIsAuthenticated(false);
  };
  const [documents, setDocuments] = useState<Document[]>([
    {
      id: '1',
      name: 'Regulamento Acadêmico 2024',
      type: 'PDF',
      // category: 'Regulamentos',
      size: '2.5 MB',
      uploadDate: '2024-01-15',
      lastModified: '2024-01-20',
      status: 'active',
      description: 'Regulamento completo dos cursos de graduação'
    },
    {
      id: '2',
      name: 'Calendário Acadêmico',
      type: 'PDF',
      // category: 'Calendários',
      size: '1.2 MB',
      uploadDate: '2024-01-10',
      lastModified: '2024-01-18',
      status: 'active',
      description: 'Datas importantes do ano letivo 2024'
    },
    {
      id: '3',
      name: 'Manual da Biblioteca',
      type: 'DOCX',
      // category: 'Manuais',
      size: '890 KB',
      uploadDate: '2024-01-08',
      lastModified: '2024-01-12',
      status: 'draft',
      description: 'Instruções para uso dos serviços da biblioteca'
    },
    {
      id: '4',
      name: 'Processo de Matrícula',
      type: 'PDF',
      // category: 'Processos',
      size: '1.8 MB',
      uploadDate: '2024-01-05',
      lastModified: '2024-01-15',
      status: 'active',
      description: 'Passo a passo para matrícula de novos alunos'
    }
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [isUploading, setIsUploading] = useState(false);

  const categories = ['Regulamentos', 'Calendários', 'Manuais', 'Processos', 'Formulários'];
  
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all';
    const matchesStatus = selectedStatus === 'all' || doc.status === selectedStatus;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    setIsUploading(true);
    
    // Simular upload
    setTimeout(() => {
      Array.from(files).forEach(file => {
        const newDoc: Document = {
          id: Date.now().toString(),
          name: file.name,
          type: file.name.split('.').pop()?.toUpperCase() || 'UNKNOWN',
          // category: 'Manuais',
          size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
          uploadDate: new Date().toISOString().split('T')[0],
          lastModified: new Date().toISOString().split('T')[0],
          status: 'draft',
          description: 'Documento adicionado recentemente'
        };
        setDocuments(prev => [newDoc, ...prev]);
      });
      setIsUploading(false);
    }, 2000);
  };

  const deleteDocument = (id: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== id));
  };

  const updateDocumentStatus = (id: string, status: 'active' | 'draft' | 'archived') => {
    setDocuments(prev => prev.map(doc => 
      doc.id === id ? { ...doc, status, lastModified: new Date().toISOString().split('T')[0] } : doc
    ));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-university-green/10 text-university-green border-university-green/20';
      case 'draft': return 'bg-university-gold/10 text-university-gold border-university-gold/20';
      case 'archived': return 'bg-muted text-muted-foreground border-border';
      default: return 'bg-muted text-muted-foreground border-border';
    }
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
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="documents">Documentos</TabsTrigger>
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="settings">Configurações</TabsTrigger>
          </TabsList>

          {/* Documents Tab */}
          <TabsContent value="documents" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                  <CardTitle className="text-sm font-medium text-muted-foreground">Ativos</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-university-green">
                    {documents.filter(d => d.status === 'active').length}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Rascunhos</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-university-gold">
                    {documents.filter(d => d.status === 'draft').length}
                  </div>
                </CardContent>
              </Card>
              {/* <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Categorias</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-university-navy">
                    {/* {new Set(documents.map(d => d.category)).size} */}
                  {/* </div> */}
                {/* </CardContent> */}
              {/* </Card> */}
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
                <div className="grid grid-cols-1 md:grid-cols-21 gap-4">
                  <div>
                    <Label htmlFor="search">Buscar</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        id="search"
                        placeholder="Nome ou descrição..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 max-w-md" 
                      />
                    </div>
                  </div>
                  {/* <div>
                    <Label htmlFor="category">Categoria</Label>
                    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                      <SelectTrigger>
                        <SelectValue placeholder="Todas as categorias" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas as categorias</SelectItem>
                        {categories.map(cat => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div> */}
                  {/* <div>
                    <Label htmlFor="status">Status</Label>
                    <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                      <SelectTrigger>
                        <SelectValue placeholder="Todos os status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos os status</SelectItem>
                        <SelectItem value="active">Ativo</SelectItem>
                        <SelectItem value="draft">Rascunho</SelectItem>
                        <SelectItem value="archived">Arquivado</SelectItem>
                      </SelectContent>
                    </Select>
                  </div> */}
                  {/* <div className="flex items-end">
                    <Button
                      onClick={() => {
                        setSearchTerm('');
                        setSelectedCategory('all');
                        setSelectedStatus('all');
                      }}
                      variant="outline"
                      className="w-full"
                    >
                      Limpar Filtros
                    </Button>
                  </div> */}
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
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredDocuments.map((doc) => (
                    <div key={doc.id} className="border rounded-lg p-4 hover:bg-muted/50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <FileText className="w-5 h-5 text-university-blue" />
                            <h3 className="font-semibold">{doc.name}</h3>
                            <Badge className={getStatusColor(doc.status)}>
                              {doc.status === 'active' ? 'Ativo' : doc.status === 'draft' ? 'Rascunho' : 'Arquivado'}
                            </Badge>
                            <Badge variant="outline">{doc.type}</Badge>
                            {/* <Badge variant="secondary">{doc.category}</Badge> */}
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">{doc.description}</p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              Upload: {new Date(doc.uploadDate).toLocaleDateString('pt-BR')}
                            </span>
                            <span>Tamanho: {doc.size}</span>
                            <span>Modificado: {new Date(doc.lastModified).toLocaleDateString('pt-BR')}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button size="sm" variant="outline">
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button size="sm" variant="outline">
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button size="sm" variant="outline">
                            <Download className="w-4 h-4" />
                          </Button>
                          <Select value={doc.status} onValueChange={(value: any) => updateDocumentStatus(doc.id, value)}>
                            <SelectTrigger className="w-32">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="active">Ativo</SelectItem>
                              <SelectItem value="draft">Rascunho</SelectItem>
                              <SelectItem value="archived">Arquivado</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => deleteDocument(doc.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                  
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
                    Formatos aceitos: PDF, DOC, DOCX, TXT (máx. 10MB cada)
                  </p>
                </div>

                {/* Upload Form */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    {/* <div>
                      <Label htmlFor="doc-category">Categoria</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione uma categoria" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map(cat => (
                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div> */}
                    <div>
                      <Label htmlFor="doc-status">Status Inicial</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione o status" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="draft">Rascunho</SelectItem>
                          <SelectItem value="active">Ativo</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
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
                      <Input id="chunk-size" defaultValue="1000" type="number" />
                      <p className="text-xs text-muted-foreground mt-1">
                        Número de caracteres por fragmento de texto
                      </p>
                    </div>
                    <div>
                      <Label htmlFor="overlap">Sobreposição</Label>
                      <Input id="overlap" defaultValue="200" type="number" />
                      <p className="text-xs text-muted-foreground mt-1">
                        Caracteres de sobreposição entre chunks
                      </p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Busca</h3>
                    <div>
                      <Label htmlFor="similarity-threshold">Modelo de embedding</Label>
                      <Input id="similarity-threshold" defaultValue="Qwen/Qwen3-Embedding-0.6B" type="text" />
                      <p className="text-xs text-muted-foreground mt-1">
                        Modelo responsável por criar o banco de dados vetorial
                      </p>
                    </div>
                    <div>
                      <Label htmlFor="max-results">Máximo de Resultados</Label>
                      <Input id="max-results" defaultValue="5" type="number" />
                      <p className="text-xs text-muted-foreground mt-1">
                        Número máximo de documentos a retornar
                      </p>
                    </div>
                  </div>
                </div>
                <div className="pt-6 border-t">
                  <Button className="bg-university-blue hover:bg-university-blue-dark">
                    Salvar Configurações
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
