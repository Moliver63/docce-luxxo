document.addEventListener('DOMContentLoaded', function () {
    const joiasContainer = document.getElementById('joiasContainer');

    // Carregar joias
    async function loadJoias(categoria = 'todos') {
        try {
            const response = await fetch(`/filtrar/${categoria}`);
            const data = await response.json();

            joiasContainer.innerHTML = '';
            data.forEach(joia => {
                const joiaCard = `
                    <div class="joia-card">
                        <img src="${joia.foto}" alt="${joia.nome}">
                        <h3>${joia.nome}</h3>
                        <p>${joia.descricao}</p>
                        <p>R$ ${joia.preco.toFixed(2)}</p>
                    </div>
                `;
                joiasContainer.innerHTML += joiaCard;
            });
        } catch (error) {
            console.error('Erro ao carregar joias:', error);
        }
    }

    // Carregar joias ao iniciar
    loadJoias();

    // Filtrar joias
    document.querySelectorAll('.filtro-btn').forEach(button => {
        button.addEventListener('click', function () {
            document.querySelector('.filtro-btn.active').classList.remove('active');
            this.classList.add('active');
            const categoria = this.dataset.categoria;
            loadJoias(categoria);
        });
    });

    // Processar upload de joias
    document.getElementById('uploadForm').addEventListener('submit', async function (e) {
        e.preventDefault();
        const formData = new FormData(this);

        try {
            const response = await fetch('/add_joia', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                loadJoias(); // Recarrega as joias após o upload
            } else {
                alert(result.error);
            }
        } catch (error) {
            console.error('Erro ao adicionar joia:', error);
        }
    });
});