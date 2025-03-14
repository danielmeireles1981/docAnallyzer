let filename = "";

async function uploadPDF() {
    const fileInput = document.getElementById("pdfFile").files[0];
    if (!fileInput) return alert("Por favor, selecione um arquivo PDF!");

    let formData = new FormData();
    formData.append("file", fileInput);

    try {
        const response = await fetch("http://127.0.0.1:8000/upload/", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        filename = data.filename;
        alert("📄 PDF enviado com sucesso!");
    } catch (error) {
        alert("❌ Erro ao enviar o PDF!");
        console.error(error);
    }
}

async function askQuestion() {
    const question = document.getElementById("question").value;
    if (!question || !filename) return alert("Primeiro envie um PDF e digite uma pergunta!");

    let formData = new FormData();
    formData.append("filename", filename);
    formData.append("question", question);

    try {
        const response = await fetch("http://127.0.0.1:8000/ask/", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        document.getElementById("response").innerText = data.answer;
    } catch (error) {
        alert("❌ Erro ao consultar a IA!");
        console.error(error);
    }
}
