import { StatusBar } from 'expo-status-bar';
import { Text, View, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, Alert, Linking } from 'react-native';
import { useState, useMemo } from 'react';
import axios from 'axios';
import { API_URL, ENDPOINTS } from './config';
import { styles } from './styles/app.styles';

export default function App() {
  const [cpf, setCpf] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedMonths, setExpandedMonths] = useState({});

  // Formata o CPF enquanto o usuário digita
  const handleCpfChange = (text) => {
    // Remove qualquer caractere que não seja número
    const numbers = text.replace(/[^\d]/g, '');
    
    // Aplicar máscara de CPF (000.000.000-00)
    let formatted = '';
    if (numbers.length <= 3) {
      formatted = numbers;
    } else if (numbers.length <= 6) {
      formatted = `${numbers.slice(0, 3)}.${numbers.slice(3)}`;
    } else if (numbers.length <= 9) {
      formatted = `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`;
    } else {
      formatted = `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9, 11)}`;
    }
    
    setCpf(formatted);
  };

  // Função para buscar informações do CPF
  const fetchCpfInfo = async () => {
    // Remove a formatação do CPF para enviar somente números
    const cleanCpf = cpf.replace(/[^\d]/g, '');
    
    // Validação básica
    if (cleanCpf.length !== 11) {
      Alert.alert('Erro', 'CPF inválido. Por favor, digite um CPF válido.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Primeiro, verificar o status do token
      const tokenStatusResponse = await axios.get(
        `${API_URL}${ENDPOINTS.TOKEN_STATUS}`
      ).catch(error => {
        // Se houver erro na verificação do token, prosseguimos com a requisição normal
        // O backend vai tentar renovar o token durante a chamada principal
        console.log('Erro ao verificar status do token:', error);
        return { data: { valid: true } };
      });
      
      // Se o token não for válido e não puder ser renovado automaticamente
      if (tokenStatusResponse.data && 
          tokenStatusResponse.data.status === 'invalid' && 
          tokenStatusResponse.data.auth_required) {
            
        // Notifica o usuário sobre a necessidade de reautorização
        Alert.alert(
          'Autorização necessária',
          'A conexão com o Bling precisa ser renovada. Deseja fazer isso agora?',
          [
            {
              text: 'Cancelar',
              style: 'cancel',
              onPress: () => {
                setLoading(false);
                setError('Operação cancelada. A autorização com o Bling é necessária para continuar.');
              }
            },
            {
              text: 'Autorizar',
              onPress: async () => {
                // Redireciona para a URL de autorização (em um navegador externo ou WebView)
                if (tokenStatusResponse.data.authorization_url) {
                  // Em um ambiente real, aqui você abriria o navegador ou WebView
                  // com a URL de autorização
                  Alert.alert(
                    'Redirecionamento',
                    'Você será redirecionado para autorizar o acesso ao Bling. Após autorizar, retorne ao aplicativo.',
                    [
                      {
                        text: 'OK',
                        onPress: () => {
                          // Abre o navegador com a URL de autorização
                          Linking.openURL(tokenStatusResponse.data.authorization_url)
                            .catch(err => {
                              console.error('Erro ao abrir URL:', err);
                              setError('Não foi possível abrir a página de autorização. Tente novamente mais tarde.');
                            });
                          setLoading(false);
                          setError('Após autorizar o acesso no Bling, tente novamente.');
                        }
                      }
                    ]
                  );
                } else {
                  setLoading(false);
                  setError('Não foi possível obter a URL de autorização.');
                }
              }
            }
          ]
        );
        return;
      }
      
      // Prossegue com a consulta normal
      const response = await axios.get(
        `${API_URL}${ENDPOINTS.CPF_SEARCH_COMPLETE}?cpf=${cleanCpf}`
      );
      
      console.log('Resposta da API:', response.data);
      
      // Processando a resposta para manter compatibilidade com o formato esperado pelo componente
      const processedResult = {
        contato: response.data.data && response.data.data.length > 0 ? response.data.data[0] : null,
        contas_a_receber: response.data.contas_a_receber || [],
        contato_detalhes: response.data.contato_detalhes || {}
      };
      
      setResult(processedResult);
    } catch (err) {
      console.error('Erro ao buscar dados:', err);
      
      // Detecta especificamente erros de autenticação (401)
      if (err.response && err.response.status === 401) {
        // Verifica se o erro indica necessidade de reautorização
        const needsAuth = err.response.data && err.response.data.auth_required;
        const authUrl = err.response.data && err.response.data.authorization_url;
        
        if (needsAuth && authUrl) {
          Alert.alert(
            'Autorização necessária',
            'A conexão com o Bling precisa ser renovada. Deseja fazer isso agora?',
            [
              {
                text: 'Cancelar',
                style: 'cancel',
                onPress: () => {
                  setError('Operação cancelada. A autorização com o Bling é necessária para continuar.');
                }
              },
              {
                text: 'Autorizar',
                onPress: () => {
                  // Abre o navegador com a URL de autorização
                  Linking.openURL(authUrl)
                    .catch(err => {
                      console.error('Erro ao abrir URL:', err);
                      setError('Não foi possível abrir a página de autorização. Tente novamente mais tarde.');
                    });
                  setError('Após autorizar o acesso no Bling, tente novamente.');
                }
              }
            ]
          );
        } else {
          setError('Erro de autenticação. A conexão com o Bling pode ter expirado.');
        }
      } else {
        // Outros erros
        setError(
          err.response?.data?.error || 
          'Ocorreu um erro ao consultar o CPF. Tente novamente mais tarde.'
        );
      }
      
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  // Formata valores monetários para exibição
  const formatCurrency = (value) => {
    if (!value && value !== 0) return '---';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  // Formata percentual para exibição
  const formatPercentage = (value) => {
    if (!value && value !== 0) return '---';
    return new Intl.NumberFormat('pt-BR', {
      style: 'percent',
      minimumFractionDigits: 0,
      maximumFractionDigits: 1
    }).format(value);
  };

  // Calcula o percentual de utilização do limite de crédito
  const calculateCreditUsagePercentage = () => {
    if (!result || !result.contato_detalhes || !result.contato_detalhes.financeiro) return null;
    
    const limiteCredito = result.contato_detalhes.financeiro?.limiteCredito || 0;
    
    // Calcula o total das contas a receber em aberto
    const totalReceberEmAberto = result.contas_a_receber
      ? result.contas_a_receber
          .filter(conta => conta.situacao === 1 || conta.situacao === 'aberto')
          .reduce((total, conta) => total + (conta.valor || 0), 0)
      : 0;
    
    // Se não há limite de crédito, retorna 1 (100%)
    if (limiteCredito === 0) return 1;
    
    // Calcula o percentual utilizado
    const percentualUtilizado = totalReceberEmAberto / limiteCredito;
    
    return percentualUtilizado;
  };

  // Determina a cor do indicador de limite de crédito com base no percentual utilizado
  const getCreditLimitColor = (percentage) => {
    if (percentage === null) return '#999'; // Cinza para desconhecido
    if (percentage >= 1) return '#FF3B30'; // Vermelho para 100% ou acima
    if (percentage >= 0.8) return '#FF9500'; // Laranja para 80% ou acima
    return '#34C759'; // Verde para menos de 80%
  };

  // Formata data para padrão brasileiro
  const formatDate = (dateString) => {
    if (!dateString) return '---';
    
    // Verificar se a data é válida e convertê-la corretamente
    try {
      // Extrai os componentes da data (formato esperado: YYYY-MM-DD)
      const [year, month, day] = dateString.split('-');
      
      // Cria a data no formato correto
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      
      // Verifica se a data é válida
      if (isNaN(date.getTime())) {
        console.log('Data inválida:', dateString);
        return dateString; // Retorna a string original se não conseguir converter
      }
      
      // Formata para o padrão brasileiro (dia/mês/ano)
      return date.toLocaleDateString('pt-BR');
    } catch (error) {
      console.log('Erro ao processar data:', error, dateString);
      return dateString; // Em caso de erro, retorna a string original
    }
  };

  // Função para agrupar contas por mês de vencimento
  const groupAccountsByMonth = (accounts) => {
    if (!accounts || accounts.length === 0) return {};
    
    const grouped = {};
    
    accounts.forEach(account => {
      if (!account.vencimento) return;
      
      try {
        // Extrai os componentes da data (formato esperado: YYYY-MM-DD)
        const [year, month, day] = account.vencimento.split('-');
        
        // Cria a data no formato correto
        const date = new Date(parseInt(year), parseInt(month) - 1, 1); // Primeiro dia do mês
        
        // Verifica se a data é válida
        if (isNaN(date.getTime())) {
          console.log('Data inválida para agrupamento:', account.vencimento);
          return;
        }
        
        // Cria uma chave para o mês/ano (ex: "2023-05")
        const monthKey = `${year}-${month.length === 1 ? '0' + month : month}`;
        
        // Adiciona o nome do mês para exibição
        if (!grouped[monthKey]) {
          const monthName = date.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
          grouped[monthKey] = {
            monthName: monthName.charAt(0).toUpperCase() + monthName.slice(1),
            accounts: [],
            timestamp: date.getTime() // Para ordenar cronologicamente
          };
        }
        
        grouped[monthKey].accounts.push(account);
      } catch (error) {
        console.log('Erro ao agrupar conta por mês:', error, account);
      }
    });
    
    return grouped;
  };

  // Função para alternar a expansão de um mês específico
  const toggleMonthExpansion = (monthKey) => {
    setExpandedMonths(prev => ({
      ...prev,
      [monthKey]: !prev[monthKey]
    }));
  };

  // Agrupa as contas por mês usando useMemo para evitar recálculos desnecessários
  const groupedAccounts = useMemo(() => {
    if (!result || !result.contas_a_receber) return {};
    return groupAccountsByMonth(result.contas_a_receber);
  }, [result]);

  // Ordena as chaves dos meses cronologicamente
  const sortedMonthKeys = useMemo(() => {
    return Object.keys(groupedAccounts).sort((a, b) => {
      return groupedAccounts[a].timestamp - groupedAccounts[b].timestamp;
    });
  }, [groupedAccounts]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Consulta de CPF</Text>
      
      <View style={styles.inputContainer}>
        <Text style={styles.label}>Digite o CPF:</Text>
        <TextInput
          style={styles.input}
          placeholder="000.000.000-00"
          keyboardType="numeric"
          maxLength={14}
          value={cpf}
          onChangeText={handleCpfChange}
        />
        <TouchableOpacity 
          style={styles.button} 
          onPress={fetchCpfInfo}
          disabled={loading}
        >
          <Text style={styles.buttonText}>Consultar</Text>
        </TouchableOpacity>
      </View>
      
      {loading ? (
        <ActivityIndicator size="large" color="#0066cc" style={styles.loader} />
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : result ? (
        <ScrollView style={styles.resultContainer}>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Informações do Contato</Text>
            <Text style={styles.contactInfo}>Nome: {result.contato?.nome || '---'}</Text>
            <Text style={styles.contactInfo}>CPF/CNPJ: {result.contato?.numeroDocumento || '---'}</Text>
            <Text style={styles.contactInfo}>Telefone: {result.contato?.telefone || '---'}</Text>
            <Text style={styles.contactInfo}>Email: {result.contato?.email || '---'}</Text>
            
            {/* Informações de limite de crédito */}
            {result.contato_detalhes && result.contato_detalhes.financeiro && (
              <View style={styles.creditLimitContainer}>
                <Text style={styles.creditLimitTitle}>Limite de Crédito:</Text>
                <Text style={styles.creditLimitValue}>
                  {formatCurrency(result.contato_detalhes.financeiro.limiteCredito || 0)}
                </Text>
                
                {/* Barra de progresso do limite utilizado */}
                <View style={styles.progressBarContainer}>
                  <View 
                    style={[
                      styles.progressBar, 
                      { 
                        width: `${Math.min((calculateCreditUsagePercentage() || 0) * 100, 100)}%`,
                        backgroundColor: getCreditLimitColor(calculateCreditUsagePercentage())
                      }
                    ]} 
                  />
                </View>
                
                <Text style={styles.creditUsageInfo}>
                  Utilizado: {formatPercentage(calculateCreditUsagePercentage() || 0)}
                </Text>
              </View>
            )}
          </View>

          <Text style={styles.sectionTitle}>Contas a Receber</Text>
          
          {result.contas_a_receber && result.contas_a_receber.length > 0 ? (
            sortedMonthKeys.length > 0 ? (
              sortedMonthKeys.map(monthKey => {
                const monthData = groupedAccounts[monthKey];
                const isExpanded = expandedMonths[monthKey];
                const totalAccounts = monthData.accounts.length;
                
                return (
                  <View key={monthKey} style={styles.monthGroup}>
                    <TouchableOpacity 
                      style={styles.monthHeader}
                      onPress={() => toggleMonthExpansion(monthKey)}
                    >
                      <Text style={styles.monthTitle}>{monthData.monthName}</Text>
                      <View style={{flexDirection: 'row', alignItems: 'center'}}>
                        <Text style={styles.monthSummary}>{totalAccounts} {totalAccounts === 1 ? 'conta' : 'contas'}</Text>
                        <Text style={styles.expandIcon}>{isExpanded ? ' ▼' : ' ▶'}</Text>
                      </View>
                    </TouchableOpacity>
                    
                    {isExpanded && monthData.accounts.map((conta, index) => (
                      <View key={index} style={styles.debtCard}>
                        <Text style={styles.debtTitle}>
                          {conta.descricao || `Conta #${index + 1}`}
                        </Text>
                        <View style={styles.debtDetail}>
                          <Text style={styles.debtLabel}>Valor:</Text>
                          <Text style={styles.debtValue}>{formatCurrency(conta.valor)}</Text>
                        </View>
                        <View style={styles.debtDetail}>
                          <Text style={styles.debtLabel}>Vencimento:</Text>
                          <Text style={styles.debtValue}>{formatDate(conta.vencimento)}</Text>
                        </View>
                        <View style={styles.debtDetail}>
                          <Text style={styles.debtLabel}>Status:</Text>
                          <Text style={[
                            styles.debtStatus,
                            conta.situacao === 'aberto' || conta.situacao === 1 ? styles.statusOpen : styles.statusClosed
                          ]}>
                            {typeof conta.situacao === 'string' 
                              ? conta.situacao.toUpperCase() 
                              : conta.situacao === 1 
                                ? 'EM ABERTO'
                                : conta.situacao === 2
                                  ? 'RECEBIDO'
                                  : conta.situacao === 3
                                    ? 'PARCIALMENTE RECEBIDO'
                                    : '---'}
                          </Text>
                        </View>
                      </View>
                    ))}
                  </View>
                );
              })
            ) : (
              <Text style={styles.noResultsText}>Erro ao agrupar contas por mês</Text>
            )
          ) : (
            <Text style={styles.noResultsText}>Nenhuma conta a receber encontrada</Text>
          )}
        </ScrollView>
      ) : null}
      
      <StatusBar style="auto" />
    </View>
  );
}
