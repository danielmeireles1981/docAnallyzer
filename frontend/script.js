// Variável global para armazenar o nome do arquivo enviado
let filename = "";

/**
 * Função responsável por enviar um arquivo PDF para o backend FastAPI.
 * Após o envio, o nome do arquivo é armazenado na variável global 'filename'.
 */
async function uploadPDF() {
    // Obtém o arquivo PDF selecionado pelo usuário no input HTML
    const fileInput = document.getElementById("pdfFile").files[0];

    // Se nenhum arquivo foi selecionado, exibe um alerta e interrompe a função
    if (!fileInput) return alert("Por favor, selecione um arquivo PDF!");

    // Cria um objeto FormData para enviar o arquivo via requisição HTTP
    let formData = new FormData();
    formData.append("file", fileInput); // Adiciona o arquivo ao FormData

    try {
        // Envia o arquivo para a API FastAPI no endpoint '/upload/'
        const response = await fetch("http://127.0.0.1:8000/upload/", {
            method: "POST",  // Método HTTP para envio de dados
            body: formData    // Corpo da requisição contendo o arquivo
        });

        // Converte a resposta da API para JSON
        const data = await response.json();

        // Armazena o nome do arquivo enviado para uso posterior
        filename = data.filename;

        // Exibe um alerta indicando sucesso no upload
        alert("📄 PDF enviado com sucesso!");
    } catch (error) {
        // Caso ocorra um erro na requisição, exibe um alerta e imprime o erro no console
        alert("❌ Erro ao enviar o PDF!");
        console.error(error);
    }
}

/**
 * Função responsável por enviar uma pergunta para a API FastAPI,
 * utilizando o conteúdo do PDF enviado anteriormente.
 */
async function askQuestion() {
    // Obtém a pergunta digitada pelo usuário no input HTML
    const question = document.getElementById("question").value;

    // Se não houver uma pergunta ou um PDF já enviado, exibe um alerta e interrompe a função
    if (!question || !filename) return alert("Primeiro envie um PDF e digite uma pergunta!");

    // Cria um objeto FormData para enviar os dados via requisição HTTP
    let formData = new FormData();
    formData.append("filename", filename);  // Adiciona o nome do arquivo ao FormData
    formData.append("question", question);  // Adiciona a pergunta ao FormData

    try {
        // Envia a pergunta para a API FastAPI no endpoint '/ask/'
        const response = await fetch("http://127.0.0.1:8000/ask/", {
            method: "POST",  // Método HTTP para envio de dados
            body: formData   // Corpo da requisição contendo a pergunta e o nome do arquivo
        });

        // Converte a resposta da API para JSON
        const data = await response.json();

        // Exibe a resposta da IA na página dentro do elemento <p> com id="response"
        document.getElementById("response").innerText = data.answer;
    } catch (error) {
        // Caso ocorra um erro na requisição, exibe um alerta e imprime o erro no console
        alert("❌ Erro ao consultar a IA!");
        console.error(error);
    }
}
