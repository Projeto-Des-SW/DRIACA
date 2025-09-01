import { Link } from "react-router-dom";
import { Shield, GraduationCap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";

interface HeaderProps {
  setShowChat: (value: boolean) => void;
}

export default function Header({ setShowChat }: HeaderProps) {
  return (
    <header className="border-b bg-background/80 backdrop-blur-md sticky top-0 z-50">
      <div className="w-full px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl">
              <img
                src="client/img/logo.gif"
                alt="Logo"
                className="w-20 h-20 object-contain"
              />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">
                Universidade Federal do Agreste de Pernambuco
              </h1>
              <p className="text-sm text-muted-foreground">
                Assistente Acadêmico DRIACA
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Badge className="bg-university-green/10 text-university-green border-university-green/20">
              <div className="w-2 h-2 bg-university-green rounded-full mr-2 animate-pulse"></div>
              Sistema Online
            </Badge>

            <Button
              asChild
              variant="outline"
              size="sm"
              className="border-university-blue text-university-blue hover:bg-university-blue hover:text-white"
            >
              <Link to="/admin">
                <Shield className="w-4 h-4 mr-2" />
                Admin
              </Link>
            </Button>

            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}
