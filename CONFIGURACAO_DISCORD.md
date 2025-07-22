# 🔧 Configuração do Discord Bot - Oráculo de Concursos

## ⚠️ Configuração Obrigatória dos Intents Privilegiados

Para que o bot funcione completamente, você precisa habilitar os **Message Content Intent** no Discord Developer Portal.

### 📝 Passos para Configuração:

1. **Acesse o Discord Developer Portal**
   - Vá para: https://discord.com/developers/applications/
   - Faça login com sua conta Discord

2. **Selecione sua Aplicação**
   - Clique na aplicação do seu bot (Oráculo de Concursos)

3. **Configure os Intents Privilegiados**
   - No menu lateral, clique em **"Bot"**
   - Role para baixo até a seção **"Privileged Gateway Intents"**
   - ✅ Habilite: **"Message Content Intent"**
   - Clique em **"Save Changes"**

### 🔗 Convite do Bot para Servidor

Para testar o bot em um servidor Discord:

1. **Gerar Link de Convite**
   - No Discord Developer Portal, vá em **"OAuth2" > "URL Generator"**
   - Selecione os scopes:
     - ✅ `bot`
     - ✅ `applications.commands`
   - Selecione as permissões:
     - ✅ `Send Messages`
     - ✅ `Read Message History`
     - ✅ `Use Slash Commands`
     - ✅ `Read Messages/View Channels`

2. **Convitar o Bot**
   - Copie a URL gerada
   - Abra em seu navegador
   - Selecione o servidor onde deseja adicionar o bot
   - Autorize as permissões

### 🧪 Testando o Bot

Depois de configurar e convidar o bot:

1. **Mencione o bot** em qualquer canal:
   ```
   @Oráculo de Concursos Olá! Como você pode me ajudar?
   ```

2. **Faça uma pergunta sobre concursos**:
   ```
   @Oráculo de Concursos O que é o princípio da legalidade no direito administrativo?
   ```

### 🔍 Recursos do Bot

- ✅ **Respostas inteligentes** sobre concursos públicos brasileiros
- ✅ **Sistema anti-alucinação** para maior precisão
- ✅ **Contexto de conversa** mantido por usuário
- ✅ **Especialização** em direito administrativo e constitucional
- ✅ **Respostas em português brasileiro**

### 🆘 Problemas Comuns

**Bot não responde:**
- ✅ Verifique se o Message Content Intent está habilitado
- ✅ Certifique-se de mencionar o bot (@Oráculo de Concursos)
- ✅ Verifique se o bot tem permissões no canal

**Erro de intents:**
- ✅ Confirme que salvou as alterações no Developer Portal
- ✅ Reinicie o bot após alterar os intents

---

🎯 **O bot está funcionando e pronto para ajudar na preparação para concursos públicos!**