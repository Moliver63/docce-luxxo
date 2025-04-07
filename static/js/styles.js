document.addEventListener('DOMContentLoaded', function() {
    // Pré-visualização da imagem
    const fotoInput = document.getElementById('foto');
    const preview = document.getElementById('preview');
    
    fotoInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            
            reader.addEventListener('load', function() {
                preview.style.display = 'block';
                preview.setAttribute('src', this.result);
            });
            
            reader.readAsDataURL(file);
        }
    });
    
    // Filtros
    const filtroBtns = document.querySelectorAll('.filtro-btn');
    filtroBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove a classe active de todos os botões
            filtroBtns.forEach(b => b.classList.remove('active'));
            // Adiciona a classe active apenas ao botão clicado
            this.classList.add('active');
            
            const categoria = this.getAttribute('data-categoria');
            filtrarJoias(categoria);
        });
    });
    
    // Formulário de upload
    const uploadForm = document.getElementById('uploadForm');
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Joia adicionada com sucesso!');
                uploadForm.reset();
                preview.style.display = 'none';
                carregarJoias();
            } else {
                alert('Erro ao adicionar joia: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Erro ao adicionar joia');
        });
    });
    
    // Carregar joias ao iniciar
    carregarJoias();
});

function carregarJoias() {
    fetch('/joias')
    .then(response => response.json())
    .then(joias => {
        const container = document.getElementById('joiasContainer');
        container.innerHTML = '';
        
        if (joias.length === 0) {
            container.innerHTML = '<p>Nenhuma joia cadastrada ainda.</p>';
            return;
        }
        
        joias.forEach(joia => {
            const card = document.createElement('div');
            card.className = 'joia-card';
            card.setAttribute('data-categoria', joia.categoria);
            
            card.innerHTML = `
                <img src="/uploads/${joia.foto}" alt="${joia.nome}" class="joia-img">
                <div class="joia-info">
                    <h3>${joia.nome}</h3>
                    <div class="preco">R$ ${joia.preco.toFixed(2).replace('.', ',')}</div>
                    <p class="descricao">${joia.descricao}</p>
                    <div class="categoria">${getCategoriaNome(joia.categoria)}</div>
                </div>
            `;
            
            container.appendChild(card);
        });
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('joiasContainer').innerHTML = '<p>Erro ao carregar as joias.</p>';
    });
}

function filtrarJoias(categoria) {
    const cards = document.querySelectorAll('.joia-card');
    
    cards.forEach(card => {
        if (categoria === 'todos' || card.getAttribute('data-categoria') === categoria) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function getCategoriaNome(categoria) {
    const categorias = {
        'aneis': 'Anéis',
        'brincos': 'Brincos',
        'pingentes': 'Pingentes',
        'outros': 'Outros'
    };
    
    return categorias[categoria] || categoria;
}