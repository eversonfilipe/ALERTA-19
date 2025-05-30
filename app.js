document.addEventListener('DOMContentLoaded', () => {
    // Referências aos elementos HTML
    const navConsultaBtn = document.getElementById('nav-consulta');
    const navGerenciamentoBtn = document.getElementById('nav-gerenciamento');
    const consultaSection = document.getElementById('consulta-dados');
    const gerenciamentoSection = document.getElementById('gerenciamento-dataset');

    const formFiltros = document.getElementById('form-filtros');
    const dataInicialInput = document.getElementById('data-inicial');
    const dataFinalInput = document.getElementById('data-final');
    const filtroEstadoSelect = document.getElementById('filtro-estado');
    const filtroMunicipioSelect = document.getElementById('filtro-municipio');
    const btnConsultar = document.getElementById('btn-consultar');

    const resultadosConsultaDiv = document.getElementById('resultados-consulta');
    const tabelaDadosCovid = document.getElementById('tabela-dados-covid');
    const tabelaBody = tabelaDadosCovid.querySelector('tbody');
    const paginacaoDiv = document.getElementById('paginacao');
    const loadingSpinner = document.getElementById('loading-spinner');
    const messageBox = document.getElementById('message-box');
    const messageBoxSpan = messageBox.querySelector('span');

    const btnImportarDataset = document.getElementById('btn-importar-dataset');
    const btnAtualizarDados = document.getElementById('btn-atualizar-dados');
    const btnLimparBase = document.getElementById('btn-limpar-base');
    const gerenciamentoMessageBox = document.getElementById('gerenciamento-message-box');
    const gerenciamentoMessageBoxSpan = gerenciamentoMessageBox.querySelector('span');

    // Variáveis de controle de paginação
    let currentPage = 1;
    const itemsPerPage = 10; // Número de itens por página
    let totalPages = 0;
    let currentData = []; // Armazena os dados brutos da consulta

    // Função para mostrar mensagens ao usuário
    function showMessage(box, span, message, type = 'info') {
        span.textContent = message;
        box.classList.remove('hidden', 'bg-red-100', 'border-red-400', 'text-red-700', 'bg-green-100', 'border-green-400', 'text-green-700', 'bg-blue-100', 'border-blue-400', 'text-blue-700');
        box.classList.add('block');

        if (type === 'error') {
            box.classList.add('bg-red-100', 'border-red-400', 'text-red-700');
        } else if (type === 'success') {
            box.classList.add('bg-green-100', 'border-green-400', 'text-green-700');
        } else { // info
            box.classList.add('bg-blue-100', 'border-blue-400', 'text-blue-700');
        }
        setTimeout(() => {
            box.classList.add('hidden');
        }, 5000); // Esconde a mensagem após 5 segundos
    }

    // Função para alternar entre as seções
    function showSection(sectionId) {
        if (sectionId === 'consulta-dados') {
            consultaSection.classList.remove('hidden');
            gerenciamentoSection.classList.add('hidden');
            navConsultaBtn.classList.add('active');
            navGerenciamentoBtn.classList.remove('active');
        } else {
            consultaSection.classList.add('hidden');
            gerenciamentoSection.classList.remove('hidden');
            navConsultaBtn.classList.remove('active');
            navGerenciamentoBtn.classList.add('active');
        }
    }

    // Event Listeners para navegação
    navConsultaBtn.addEventListener('click', () => showSection('consulta-dados'));
    navGerenciamentoBtn.addEventListener('click', () => showSection('gerenciamento-dataset'));

    // COMENTÁRIO_PARA_BACKEND: Função para preencher dinamicamente os estados no dropdown.
    // ENDPOINT: /api/estados
    // MÉTODO: GET
    // RESPOSTA ESPERADA: JSON Array de objetos { sigla: 'SP', nome: 'São Paulo' }
    async function preencherEstados() {
        try {
            const response = await fetch('/api/estados'); // COMENTÁRIO_PARA_BACKEND: URL do endpoint para buscar estados.
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const estados = await response.json();

            filtroEstadoSelect.innerHTML = '<option value="">Selecione um Estado</option>';
            estados.forEach(estado => {
                const option = document.createElement('option');
                option.value = estado.sigla;
                option.textContent = estado.nome;
                filtroEstadoSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Erro ao buscar estados:', error);
            showMessage(messageBox, messageBoxSpan, 'Erro ao carregar estados. Tente novamente.', 'error');
        }
    }

    // COMENTÁRIO_PARA_BACKEND: Função para preencher dinamicamente os municípios com base no estado selecionado.
    // ENDPOINT: /api/municipios?estado=<sigla_estado>
    // MÉTODO: GET
    // RESPOSTA ESPERADA: JSON Array de strings com nomes de municípios.
    async function preencherMunicipios(estadoSigla) {
        filtroMunicipioSelect.innerHTML = '<option value="">Selecione um Município</option>';
        filtroMunicipioSelect.disabled = true;
        if (!estadoSigla) {
            return;
        }
        try {
            const response = await fetch(`/api/municipios?estado=${estadoSigla}`); // COMENTÁRIO_PARA_BACKEND: URL do endpoint para buscar municípios.
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const municipios = await response.json();

            municipios.forEach(municipio => {
                const option = document.createElement('option');
                option.value = municipio;
                option.textContent = municipio;
                filtroMunicipioSelect.appendChild(option);
            });
            filtroMunicipioSelect.disabled = false;
        } catch (error) {
            console.error('Erro ao buscar municípios:', error);
            showMessage(messageBox, messageBoxSpan, 'Erro ao carregar municípios. Tente novamente.', 'error');
        }
    }

    // Event Listener para mudança de estado
    filtroEstadoSelect.addEventListener('change', (event) => {
        preencherMunicipios(event.target.value);
    });

    // COMENTÁRIO_PARA_BACKEND: Função para renderizar os dados na tabela.
    function renderTable(data) {
        tabelaBody.innerHTML = ''; // Limpa a tabela
        if (data.length === 0) {
            tabelaBody.innerHTML = `
                <tr id="no-data-row">
                    <td colspan="7" class="py-4 text-center text-gray-500">Nenhum dado encontrado para os filtros aplicados.</td>
                </tr>
            `;
            return;
        }

        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const pageData = data.slice(startIndex, endIndex);

        pageData.forEach(dado => {
            const row = document.createElement('tr');
            row.classList.add('border-b', 'border-gray-200', 'hover:bg-gray-100');
            row.innerHTML = `
                <td class="py-3 px-6 text-left whitespace-nowrap">${dado.date || 'N/A'}</td>
                <td class="py-3 px-6 text-left">${dado.state || 'N/A'}</td>
                <td class="py-3 px-6 text-left">${dado.city || 'N/A'}</td>
                <td class="py-3 px-6 text-left">${dado.confirmed_cases !== undefined ? dado.confirmed_cases : 'N/A'}</td>
                <td class="py-3 px-6 text-left">${dado.deaths !== undefined ? dado.deaths : 'N/A'}</td>
                <td class="py-3 px-6 text-left">${dado.new_cases !== undefined ? dado.new_cases : 'N/A'}</td>
                <td class="py-3 px-6 text-left">${dado.new_deaths !== undefined ? dado.new_deaths : 'N/A'}</td>
            `;
            tabelaBody.appendChild(row);
        });
    }

    // COMENTÁRIO_PARA_BACKEND: Função para renderizar os botões de paginação.
    function renderPagination() {
        paginacaoDiv.innerHTML = '';
        totalPages = Math.ceil(currentData.length / itemsPerPage);

        if (totalPages <= 1) {
            return; // Não mostra paginação se houver apenas 1 página ou menos
        }

        const createButton = (text, page, isActive = false, isDisabled = false) => {
            const button = document.createElement('button');
            button.textContent = text;
            button.classList.add('bg-gray-300', 'text-gray-800', 'font-semibold', 'py-2', 'px-4', 'rounded', 'transition', 'duration-300');
            if (isActive) {
                button.classList.add('active', 'bg-blue-500', 'text-white');
            }
            if (isDisabled) {
                button.disabled = true;
            }
            button.addEventListener('click', () => {
                currentPage = page;
                renderTable(currentData);
                renderPagination();
            });
            return button;
        };

        paginacaoDiv.appendChild(createButton('Anterior', currentPage - 1, false, currentPage === 1));

        // Lógica para mostrar um número limitado de botões de página
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, currentPage + 2);

        if (endPage - startPage < 4) { // Garante que 5 botões sejam exibidos se possível
            if (startPage === 1) {
                endPage = Math.min(totalPages, 5);
            } else if (endPage === totalPages) {
                startPage = Math.max(1, totalPages - 4);
            }
        }


        for (let i = startPage; i <= endPage; i++) {
            paginacaoDiv.appendChild(createButton(i, i, i === currentPage));
        }

        paginacaoDiv.appendChild(createButton('Próxima', currentPage + 1, false, currentPage === totalPages));
    }


    // COMENTÁRIO_PARA_BACKEND: Event Listener para o formulário de filtros (consulta).
    // ENDPOINT: /api/consulta_dados
    // MÉTODO: GET (ou POST, dependendo da complexidade dos filtros)
    // PARÂMETROS: data_inicial, data_final (YYYY-MM-DD), estado (sigla), municipio (nome)
    // RESPOSTA ESPERADA: JSON Array de objetos com os dados da COVID-19.
    formFiltros.addEventListener('submit', async (event) => {
        event.preventDefault(); // Previne o recarregamento da página

        loadingSpinner.classList.remove('hidden');
        messageBox.classList.add('hidden');
        tabelaBody.innerHTML = ''; // Limpa a tabela antes de carregar novos dados
        paginacaoDiv.innerHTML = ''; // Limpa a paginação

        const params = new URLSearchParams();
        if (dataInicialInput.value) params.append('data_inicial', dataInicialInput.value);
        if (dataFinalInput.value) params.append('data_final', dataFinalInput.value);
        if (filtroEstadoSelect.value) params.append('estado', filtroEstadoSelect.value);
        if (filtroMunicipioSelect.value) params.append('municipio', filtroMunicipioSelect.value);

        // COMENTÁRIO_PARA_BACKEND: Construção da URL para a requisição.
        const url = `/api/consulta_dados?${params.toString()}`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            currentData = await response.json(); // Armazena os dados brutos
            currentPage = 1; // Reseta a página para a primeira
            renderTable(currentData);
            renderPagination();
            if (currentData.length === 0) {
                showMessage(messageBox, messageBoxSpan, 'Nenhum dado encontrado para os filtros selecionados.', 'info');
            } else {
                showMessage(messageBox, messageBoxSpan, `Consulta realizada com sucesso! Foram encontrados ${currentData.length} registros.`, 'success');
            }

        } catch (error) {
            console.error('Erro ao consultar dados:', error);
            showMessage(messageBox, messageBoxSpan, 'Erro ao consultar dados. Verifique os filtros e tente novamente.', 'error');
        } finally {
            loadingSpinner.classList.add('hidden');
        }
    });

    // COMENTÁRIO_PARA_BACKEND: Event Listener para o botão 'Importar Novo Dataset'.
    // ENDPOINT: /api/importar_dataset
    // MÉTODO: POST
    // CORPO DA REQUISIÇÃO: Pode ser vazio ou conter um path/URL para o dataset, se aplicável.
    // RESPOSTA ESPERADA: JSON com { "status": "success", "message": "Dataset importado com sucesso." }
    btnImportarDataset.addEventListener('click', async () => {
        if (!confirm('Tem certeza que deseja importar um novo dataset? Isso pode levar algum tempo.')) {
            return;
        }

        showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, 'Importando novo dataset... Por favor, aguarde.', 'info');

        try {
            const response = await fetch('/api/importar_dataset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({}) // Pode enviar dados adicionais se necessário
            });

            const result = await response.json();
            if (response.ok) {
                showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, result.message, 'success');
            } else {
                throw new Error(result.message || 'Erro ao importar dataset.');
            }
        } catch (error) {
            console.error('Erro ao importar dataset:', error);
            showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, `Erro: ${error.message}`, 'error');
        }
    });

    // COMENTÁRIO_PARA_BACKEND: Event Listener para o botão 'Atualizar Dados Existentes'.
    // ENDPOINT: /api/atualizar_dados
    // MÉTODO: PUT
    // CORPO DA REQUISIÇÃO: Pode ser vazio ou conter critérios de atualização.
    // RESPOSTA ESPERADA: JSON com { "status": "success", "message": "Dados atualizados com sucesso." }
    btnAtualizarDados.addEventListener('click', async () => {
        if (!confirm('Tem certeza que deseja atualizar os dados existentes?')) {
            return;
        }

        showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, 'Atualizando dados existentes... Por favor, aguarde.', 'info');

        try {
            const response = await fetch('/api/atualizar_dados', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({}) // Pode enviar dados adicionais se necessário
            });

            const result = await response.json();
            if (response.ok) {
                showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, result.message, 'success');
            } else {
                throw new Error(result.message || 'Erro ao atualizar dados.');
            }
        } catch (error) {
            console.error('Erro ao atualizar dados:', error);
            showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, `Erro: ${error.message}`, 'error');
        }
    });

    // COMENTÁRIO_PARA_BACKEND: Event Listener para o botão 'Limpar Base de Dados'.
    // ENDPOINT: /api/limpar_base
    // MÉTODO: DELETE
    // CORPO DA REQUISIÇÃO: Vazio ou com confirmação.
    // RESPOSTA ESPERADA: JSON com { "status": "success", "message": "Base de dados limpa com sucesso." }
    btnLimparBase.addEventListener('click', async () => {
        if (!confirm('ATENÇÃO: Tem certeza que deseja LIMPAR TODA a base de dados? Esta ação é irreversível!')) {
            return;
        }

        showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, 'Limpando base de dados... Por favor, aguarde.', 'info');

        try {
            const response = await fetch('/api/limpar_base', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            if (response.ok) {
                showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, result.message, 'success');
                // Após limpar, talvez seja bom recarregar a seção de consulta ou exibir uma mensagem
                currentData = [];
                renderTable(currentData);
                renderPagination();
            } else {
                throw new Error(result.message || 'Erro ao limpar base de dados.');
            }
        } catch (error) {
            console.error('Erro ao limpar base de dados:', error);
            showMessage(gerenciamentoMessageBox, gerenciamentoMessageBoxSpan, `Erro: ${error.message}`, 'error');
        }
    });

    // Inicialização: Preencher estados e exibir a seção de consulta por padrão
    preencherEstados();
    showSection('consulta-dados');
});
