export function generateBotResponse(userMessage) {
  const lowerMsg = userMessage.toLowerCase();

  if (lowerMsg.includes("matrícula")) {
    return "O setor de DRCA realiza matrícula e rematrícula dos alunos.";
  }
  if (lowerMsg.includes("estágio")) {
    return "O setor de estágio cuida dos documentos e validações dos estágios supervisionados.";
  }
  if (lowerMsg.includes("aproveitamento")) {
    return "O aproveitamento de disciplina deve ser solicitado junto ao DRCA com a documentação necessária.";
  }

  return "Não tenho certeza sobre isso. Tente perguntar de outra forma!";
}
