document.addEventListener('DOMContentLoaded', () => {
  // Navigation tabs
  const navItems = document.querySelectorAll('.nav-item');
  const tabPanes = document.querySelectorAll('.tab-pane');
  
  // Overlay modal elements
  const chatOverlayModal = document.getElementById('chatOverlayModal');
  const closeChatModalBtn = document.getElementById('closeChatModalBtn');
  const clearChatMessagesBtn = document.getElementById('clearChatMessagesBtn');
  const messagesContainer = document.getElementById('messagesContainer');
  const mainChatForm = document.getElementById('mainChatForm');
  const userQuestionInput = document.getElementById('userQuestionInput');
  const suggestPromptBtn = document.getElementById('suggestPromptBtn');

  // Stats & Badges
  const sidebarFaqCount = document.getElementById('sidebarFaqCount');
  const sidebarCatCount = document.getElementById('sidebarCatCount');
  const analyticsTotalQuestions = document.getElementById('analyticsTotalQuestions');
  
  // Sliders & Forms
  const paneThresholdSlider = document.getElementById('paneThresholdSlider');
  const paneThresholdVal = document.getElementById('paneThresholdVal');
  const newFaqForm = document.getElementById('newFaqForm');
  const faqSuccessMsg = document.getElementById('faqSuccessMsg');
  const corpusListContainer = document.getElementById('corpusListContainer');
  const corpusSearchInput = document.getElementById('corpusSearchInput');
  const viewAllFaqsBtn = document.getElementById('viewAllFaqsBtn');

  // Theme switch
  const themeCheckbox = document.getElementById('themeCheckbox');
  const themeIcon = document.getElementById('themeIcon');

  let currentThreshold = 0.32;
  let allFaqsList = [];
  let totalUserQueries = 0;

  // 1. Tab Navigation
  navItems.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.dataset.tab;
      switchTab(targetTab);
    });
  });

  function switchTab(tabId) {
    navItems.forEach(item => {
      if (item.dataset.tab === tabId) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    tabPanes.forEach(pane => {
      if (pane.id === `tab-${tabId}`) {
        pane.classList.add('active');
      } else {
        pane.classList.remove('active');
      }
    });

    if (tabId === 'corpus') {
      renderCorpusList(allFaqsList);
    }
  }

  if (viewAllFaqsBtn) {
    viewAllFaqsBtn.addEventListener('click', () => {
      switchTab('corpus');
    });
  }

  // 2. Dark / Light mode toggle
  if (themeCheckbox) {
    themeCheckbox.addEventListener('change', (e) => {
      if (e.target.checked) {
        document.body.classList.remove('light-mode');
        document.body.classList.add('dark-mode');
        themeIcon.className = 'fa-solid fa-sun';
      } else {
        document.body.classList.remove('dark-mode');
        document.body.classList.add('light-mode');
        themeIcon.className = 'fa-solid fa-moon';
      }
    });
  }

  // 3. Threshold Slider
  if (paneThresholdSlider) {
    paneThresholdSlider.addEventListener('input', (e) => {
      currentThreshold = parseFloat(e.target.value);
      paneThresholdVal.textContent = currentThreshold.toFixed(2);
    });
  }

  // 4. Close & Clear Overlay Modal
  if (closeChatModalBtn) {
    closeChatModalBtn.addEventListener('click', () => {
      chatOverlayModal.style.display = 'none';
    });
  }

  if (clearChatMessagesBtn) {
    clearChatMessagesBtn.addEventListener('click', () => {
      messagesContainer.innerHTML = '';
      chatOverlayModal.style.display = 'none';
    });
  }

  // 5. Popular Questions Cards Click
  document.querySelectorAll('.popular-card').forEach(card => {
    card.addEventListener('click', () => {
      const query = card.dataset.query;
      if (query) {
        sendUserMessage(query);
      }
    });
  });

  // 6. Category Cards Click
  document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', () => {
      const cat = card.dataset.cat;
      const matched = allFaqsList.filter(f => f.category === cat);
      if (matched.length > 0) {
        sendUserMessage(matched[0].question);
      } else {
        sendUserMessage(`Tell me about ${card.querySelector('h4').innerText}`);
      }
    });
  });

  // 7. Paperclip / Suggest button
  if (suggestPromptBtn) {
    suggestPromptBtn.addEventListener('click', () => {
      const suggestions = [
        "How can I track my order?",
        "What is your return policy?",
        "Do you accept PayPal or Apple Pay?",
        "How long does a refund take?",
        "Do you ship internationally?"
      ];
      const randomSugg = suggestions[Math.floor(Math.random() * suggestions.length)];
      userQuestionInput.value = randomSugg;
      userQuestionInput.focus();
    });
  }

  // 8. Main Form Submit
  if (mainChatForm) {
    mainChatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = userQuestionInput.value.trim();
      if (!text) return;
      sendUserMessage(text);
    });
  }

  // 9. Send User Message & Display ONLY Clean Answer
  async function sendUserMessage(questionText) {
    switchTab('home');

    // Show the floating chat modal
    chatOverlayModal.style.display = 'flex';

    // Append user question
    appendMessage(questionText, 'user');
    userQuestionInput.value = '';
    userQuestionInput.focus();

    // Show typing indicator
    const typingId = appendTypingIndicator();

    totalUserQueries++;
    if (analyticsTotalQuestions) {
      analyticsTotalQuestions.textContent = totalUserQueries;
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: questionText,
          threshold: currentThreshold
        })
      });

      const data = await response.json();
      removeTypingIndicator(typingId);

      if (data.error) {
        appendBotAnswer("Sorry, I encountered an issue processing your question. Please try again.", []);
        return;
      }

      // DISPLAY ONLY CLEAN ANSWER (NO vector analysis or code!)
      appendBotAnswer(data.answer, data.suggestions);

    } catch (err) {
      removeTypingIndicator(typingId);
      appendBotAnswer("Unable to reach the support server. Please make sure the app is running.", []);
      console.error(err);
    }
  }

  function appendMessage(text, sender) {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msgDiv = document.createElement('div');
    msgDiv.className = `message-item ${sender}`;

    const avatarIcon = sender === 'user' 
      ? '<i class="fa-solid fa-user"></i>' 
      : '<i class="fa-solid fa-robot"></i>';

    msgDiv.innerHTML = `
      <div class="msg-avatar">${avatarIcon}</div>
      <div class="msg-content">
        <div class="msg-bubble">${escapeHtml(text)}</div>
        <div class="msg-time">${time}</div>
      </div>
    `;

    messagesContainer.appendChild(msgDiv);
    scrollChatBottom();
  }

  function appendBotAnswer(answerText, suggestions) {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message-item bot';

    let suggestionsHtml = '';
    if (suggestions && suggestions.length > 0) {
      const chips = suggestions.slice(0, 3).map(s => `
        <button class="suggestion-chip" data-query="${escapeHtml(s)}">
          💡 "${escapeHtml(s)}"
        </button>
      `).join('');

      suggestionsHtml = `
        <div class="chat-suggestions">
          <span class="chat-suggestions-title">Related questions:</span>
          ${chips}
        </div>
      `;
    }

    msgDiv.innerHTML = `
      <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
      <div class="msg-content">
        <div class="msg-bubble">
          <div>${formatCleanText(answerText)}</div>
          ${suggestionsHtml}
        </div>
        <div class="msg-time">${time}</div>
      </div>
    `;

    messagesContainer.appendChild(msgDiv);
    scrollChatBottom();

    // Attach click events for suggestion chips
    msgDiv.querySelectorAll('.suggestion-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        sendUserMessage(btn.dataset.query);
      });
    });
  }

  function appendTypingIndicator() {
    const id = 'typing-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = id;
    msgDiv.className = 'message-item bot';
    msgDiv.innerHTML = `
      <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
      <div class="msg-content">
        <div class="msg-bubble" style="padding: 10px 16px; color: var(--text-secondary); font-size: 0.85rem;">
          <i class="fa-solid fa-circle-notch fa-spin"></i> Finding best answer...
        </div>
      </div>
    `;
    messagesContainer.appendChild(msgDiv);
    scrollChatBottom();
    return id;
  }

  function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function formatCleanText(str) {
    if (!str) return '';
    let formatted = str.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\n• (.*?)(?=\n|$)/g, '<br>• $1');
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
  }

  function scrollChatBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // 10. Load Initial FAQs
  async function loadInitialData() {
    try {
      const res = await fetch('/api/faqs');
      const data = await res.json();
      
      const categories = Object.keys(data.categories || {});
      allFaqsList = [];
      for (const cat of categories) {
        allFaqsList.push(...data.categories[cat]);
      }

      if (sidebarFaqCount) sidebarFaqCount.textContent = allFaqsList.length;
      if (sidebarCatCount) sidebarCatCount.textContent = categories.length;

      renderCorpusList(allFaqsList);
    } catch (err) {
      console.error('Error loading initial FAQs:', err);
    }
  }

  function renderCorpusList(faqs) {
    if (!corpusListContainer) return;
    if (faqs.length === 0) {
      corpusListContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 20px;">No FAQs found.</p>';
      return;
    }

    corpusListContainer.innerHTML = faqs.map(f => `
      <div class="faq-item-card">
        <h4><i class="fa-regular fa-circle-question" style="color: var(--accent-cyan);"></i> ${escapeHtml(f.question)}</h4>
        <p>${escapeHtml(f.answer)}</p>
        <div>
          <span class="faq-tag-pill" style="color: var(--accent-purple); font-weight: 600;">${escapeHtml(f.category || 'General')}</span>
          ${(f.tags || []).map(t => `<span class="faq-tag-pill">#${escapeHtml(t)}</span>`).join('')}
        </div>
      </div>
    `).join('');
  }

  // Search Filter
  if (corpusSearchInput) {
    corpusSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      const filtered = allFaqsList.filter(f => 
        f.question.toLowerCase().includes(query) || 
        f.answer.toLowerCase().includes(query) ||
        (f.tags || []).some(t => t.toLowerCase().includes(query))
      );
      renderCorpusList(filtered);
    });
  }

  // 11. FAQ Management Form
  if (newFaqForm) {
    newFaqForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = document.getElementById('newQuestion').value.trim();
      const category = document.getElementById('newCategory').value;
      const answer = document.getElementById('newAnswer').value.trim();
      const tagsStr = document.getElementById('newTags').value.trim();
      const tags = tagsStr.split(',').map(t => t.trim()).filter(Boolean);

      try {
        const res = await fetch('/api/add_faq', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question, category, answer, tags })
        });
        const data = await res.json();

        if (data.success) {
          faqSuccessMsg.textContent = '✅ New FAQ successfully added and indexed into the NLP knowledge base!';
          faqSuccessMsg.style.display = 'block';
          newFaqForm.reset();
          loadInitialData();
          setTimeout(() => {
            faqSuccessMsg.style.display = 'none';
          }, 4000);
        }
      } catch (err) {
        console.error('Failed to add FAQ:', err);
      }
    });
  }

  // Deploy notice
  const deployBtn = document.getElementById('deployBtn');
  if (deployBtn) {
    deployBtn.addEventListener('click', () => {
      alert('🚀 Bot is live and actively serving requests on http://127.0.0.1:5000!');
    });
  }

  // Initialize
  loadInitialData();
});
