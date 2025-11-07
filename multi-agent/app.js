const { createApp } = Vue;

createApp({
    data() {
        return {
            // UI State
            showSettings: false,
            showAddAgent: false,
            isRunning: false,
            currentAgent: '',

            // Configuration
            topic: '',
            maxRounds: 3,

            // API Keys
            apiKeys: {
                openai: '',
                claude: '',
                deepseek: ''
            },

            // Agents
            agents: [],
            newAgent: {
                name: '',
                model: 'gpt-5',
                role: '',
                isSummarizer: false
            },

            // Discussion
            discussion: [],
            shouldStop: false,

            // Agent colors
            agentColors: [
                '#3B82F6', '#8B5CF6', '#EC4899', '#10B981',
                '#F59E0B', '#EF4444', '#06B6D4', '#84CC16'
            ]
        };
    },

    mounted() {
        this.loadApiKeys();
        this.loadAgents();
        this.loadDiscussion();
    },

    methods: {
        // ============ API Keys Management ============
        saveApiKeys() {
            localStorage.setItem('apiKeys', JSON.stringify(this.apiKeys));
            this.showSettings = false;
            alert('API Keys 已保存');
        },

        loadApiKeys() {
            const saved = localStorage.getItem('apiKeys');
            if (saved) {
                this.apiKeys = JSON.parse(saved);
            }
        },

        // ============ Agent Management ============
        addAgent() {
            this.newAgent = {
                name: '',
                model: 'gpt-5',
                role: '',
                isSummarizer: false
            };
            this.showAddAgent = true;
        },

        confirmAddAgent() {
            if (!this.newAgent.name || !this.newAgent.role) {
                alert('请填写完整的角色信息');
                return;
            }

            const agent = {
                ...this.newAgent,
                color: this.getRandomColor()
            };

            this.agents.push(agent);
            this.saveAgents();
            this.showAddAgent = false;
        },

        removeAgent(index) {
            if (confirm('确定要删除这个角色吗？')) {
                this.agents.splice(index, 1);
                this.saveAgents();
            }
        },

        saveAgents() {
            localStorage.setItem('agents', JSON.stringify(this.agents));
        },

        loadAgents() {
            const saved = localStorage.getItem('agents');
            if (saved) {
                this.agents = JSON.parse(saved);
            } else {
                // Default medical scenario agents
                this.agents = [
                    {
                        name: 'SurgeonGPT',
                        model: 'gpt-5',
                        role: '资深外科主任医师，擅长妇科肿瘤手术，有20年临床经验，负责制定手术方案',
                        color: 'from-blue-50 to-blue-100 border-blue-500',
                        isSummarizer: false
                    },
                    {
                        name: 'PathologistGPT',
                        model: 'gpt-5-mini',
                        role: '病理科专家，负责分析病理报告，评估肿瘤分期和侵袭程度',
                        color: 'from-purple-50 to-purple-100 border-purple-500',
                        isSummarizer: false
                    },
                    {
                        name: 'RadiologistGPT',
                        model: 'gpt-5-nano',
                        role: '影像科医生，负责解读CT、MRI等影像学检查，评估肿瘤范围',
                        color: 'from-pink-50 to-pink-100 border-pink-500',
                        isSummarizer: false
                    },
                    {
                        name: 'ChiefGPT',
                        model: 'gpt-5',
                        role: '科室主任，负责综合各专家意见，做出最终决策和总结',
                        color: 'from-green-50 to-green-100 border-green-500',
                        isSummarizer: true
                    }
                ];
                this.saveAgents();
            }
        },

        getRandomColor() {
            const colors = [
                'from-blue-50 to-blue-100 border-blue-500',
                'from-purple-50 to-purple-100 border-purple-500',
                'from-pink-50 to-pink-100 border-pink-500',
                'from-green-50 to-green-100 border-green-500',
                'from-yellow-50 to-yellow-100 border-yellow-500',
                'from-red-50 to-red-100 border-red-500',
                'from-indigo-50 to-indigo-100 border-indigo-500',
                'from-teal-50 to-teal-100 border-teal-500'
            ];
            return colors[Math.floor(Math.random() * colors.length)];
        },

        getAgentColor(agentName) {
            const index = this.agents.findIndex(a => a.name === agentName);
            return this.agentColors[index % this.agentColors.length];
        },

        // ============ Discussion Flow ============
        async startDiscussion() {
            if (!this.validateSetup()) return;

            this.isRunning = true;
            this.shouldStop = false;
            this.discussion = [];

            try {
                // Get regular agents (non-summarizers)
                const regularAgents = this.agents.filter(a => !a.isSummarizer);
                const summarizerAgents = this.agents.filter(a => a.isSummarizer);

                // Run discussion rounds
                for (let round = 1; round <= this.maxRounds; round++) {
                    if (this.shouldStop) break;

                    for (const agent of regularAgents) {
                        if (this.shouldStop) break;

                        this.currentAgent = agent.name;
                        const context = this.buildContext(agent, round);
                        const reply = await this.callModel(agent.model, agent.role, context);

                        this.discussion.push({
                            round: round,
                            speaker: agent.name,
                            text: reply,
                            timestamp: new Date().toISOString()
                        });

                        this.saveDiscussion();
                        this.scrollToBottom();
                    }
                }

                // Final summary by summarizer agents
                if (!this.shouldStop && summarizerAgents.length > 0) {
                    for (const agent of summarizerAgents) {
                        if (this.shouldStop) break;

                        this.currentAgent = agent.name;
                        const summaryContext = this.buildSummaryContext(agent);
                        const summary = await this.callModel(agent.model, agent.role, summaryContext);

                        this.discussion.push({
                            speaker: agent.name,
                            text: summary,
                            isSummary: true,
                            timestamp: new Date().toISOString()
                        });

                        this.saveDiscussion();
                        this.scrollToBottom();
                    }
                }
            } catch (error) {
                console.error('Discussion error:', error);
                alert(`讨论过程出错: ${error.message}`);
            } finally {
                this.isRunning = false;
                this.currentAgent = '';
            }
        },

        stopDiscussion() {
            this.shouldStop = true;
            this.isRunning = false;
        },

        clearDiscussion() {
            if (confirm('确定要清空所有讨论记录吗？')) {
                this.discussion = [];
                this.saveDiscussion();
            }
        },

        validateSetup() {
            if (!this.topic) {
                alert('请输入讨论主题');
                return false;
            }

            if (this.agents.length < 2) {
                alert('至少需要2个角色才能开始讨论');
                return false;
            }

            // Check if API keys are configured
            const models = this.agents.map(a => a.model);
            const needsOpenAI = models.some(m => m.startsWith('gpt'));
            const needsClaude = models.some(m => m.startsWith('claude'));
            const needsDeepSeek = models.some(m => m.startsWith('deepseek'));

            if (needsOpenAI && !this.apiKeys.openai) {
                alert('请先配置 OpenAI API Key');
                this.showSettings = true;
                return false;
            }

            if (needsClaude && !this.apiKeys.claude) {
                alert('请先配置 Claude API Key');
                this.showSettings = true;
                return false;
            }

            if (needsDeepSeek && !this.apiKeys.deepseek) {
                alert('请先配置 DeepSeek API Key');
                this.showSettings = true;
                return false;
            }

            return true;
        },

        // ============ Context Building ============
        buildContext(agent, round) {
            let context = `当前讨论主题: ${this.topic}\n\n`;
            context += `你是${agent.name}，角色定位: ${agent.role}\n\n`;

            if (this.discussion.length > 0) {
                context += `以下是之前的讨论内容：\n\n`;

                // Get previous rounds' discussions
                const previousDiscussions = this.discussion.filter(d => d.round && d.round < round);
                const currentRoundDiscussions = this.discussion.filter(d => d.round === round);

                if (previousDiscussions.length > 0) {
                    previousDiscussions.forEach(msg => {
                        context += `【第${msg.round}轮】${msg.speaker}: ${msg.text}\n\n`;
                    });
                }

                if (currentRoundDiscussions.length > 0) {
                    context += `【当前第${round}轮的其他专家意见】:\n`;
                    currentRoundDiscussions.forEach(msg => {
                        context += `${msg.speaker}: ${msg.text}\n\n`;
                    });
                }
            }

            context += `现在是第${round}轮讨论（共${this.maxRounds}轮），请基于你的专业角色，`;

            if (round === 1) {
                context += `提出你的初步意见和建议。`;
            } else {
                context += `参考之前的讨论内容，补充、修正或深化你的观点。`;
            }

            return context;
        },

        buildSummaryContext(agent) {
            let context = `讨论主题: ${this.topic}\n\n`;
            context += `你是${agent.name}，角色定位: ${agent.role}\n\n`;
            context += `经过${this.maxRounds}轮讨论，各专家的意见如下：\n\n`;

            // Organize by rounds
            for (let r = 1; r <= this.maxRounds; r++) {
                const roundMsgs = this.discussion.filter(d => d.round === r);
                if (roundMsgs.length > 0) {
                    context += `\n=== 第${r}轮讨论 ===\n`;
                    roundMsgs.forEach(msg => {
                        context += `\n${msg.speaker}:\n${msg.text}\n`;
                    });
                }
            }

            context += `\n\n请你作为最终决策者，综合所有专家的意见，给出：\n`;
            context += `1. 核心结论和最终方案\n`;
            context += `2. 关键要点总结\n`;
            context += `3. 需要注意的风险和建议\n`;
            context += `4. 具体的执行步骤（如适用）\n\n`;
            context += `请给出清晰、结构化的最终总结。`;

            return context;
        },

        // ============ AI Model API Calls ============
        async callModel(model, role, userMessage) {
            if (model.startsWith('gpt')) {
                return await this.callOpenAI(model, role, userMessage);
            } else if (model.startsWith('claude')) {
                return await this.callClaude(model, role, userMessage);
            } else if (model.startsWith('deepseek')) {
                return await this.callDeepSeek(model, role, userMessage);
            } else {
                throw new Error(`Unsupported model: ${model}`);
            }
        },

        async callOpenAI(model, systemPrompt, userMessage) {
            const response = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKeys.openai}`
                },
                body: JSON.stringify({
                    model: model,
                    messages: [
                        { role: 'system', content: systemPrompt },
                        { role: 'user', content: userMessage }
                    ],
                    temperature: 0.7,
                    max_tokens: 1500
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(`OpenAI API Error: ${error.error?.message || response.statusText}`);
            }

            const data = await response.json();
            return data.choices[0].message.content;
        },

        async callClaude(model, systemPrompt, userMessage) {
            const response = await fetch('https://api.anthropic.com/v1/messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': this.apiKeys.claude,
                    'anthropic-version': '2023-06-01'
                },
                body: JSON.stringify({
                    model: model,
                    max_tokens: 1500,
                    system: systemPrompt,
                    messages: [
                        { role: 'user', content: userMessage }
                    ],
                    temperature: 0.7
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(`Claude API Error: ${error.error?.message || response.statusText}`);
            }

            const data = await response.json();
            return data.content[0].text;
        },

        async callDeepSeek(model, systemPrompt, userMessage) {
            const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKeys.deepseek}`
                },
                body: JSON.stringify({
                    model: model,
                    messages: [
                        { role: 'system', content: systemPrompt },
                        { role: 'user', content: userMessage }
                    ],
                    temperature: 0.7,
                    max_tokens: 1500
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(`DeepSeek API Error: ${error.error?.message || response.statusText}`);
            }

            const data = await response.json();
            return data.choices[0].message.content;
        },

        // ============ Storage ============
        saveDiscussion() {
            localStorage.setItem('discussion', JSON.stringify(this.discussion));
            localStorage.setItem('topic', this.topic);
        },

        loadDiscussion() {
            const savedDiscussion = localStorage.getItem('discussion');
            const savedTopic = localStorage.getItem('topic');

            if (savedDiscussion) {
                this.discussion = JSON.parse(savedDiscussion);
            }

            if (savedTopic) {
                this.topic = savedTopic;
            }
        },

        // ============ Export ============
        exportDiscussion() {
            const markdown = this.generateMarkdown();
            const blob = new Blob([markdown], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `讨论记录_${this.topic}_${new Date().toISOString().slice(0, 10)}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        },

        generateMarkdown() {
            let md = `# ${this.topic}\n\n`;
            md += `**讨论时间**: ${new Date().toLocaleString('zh-CN')}\n\n`;
            md += `**讨论轮数**: ${this.maxRounds}\n\n`;
            md += `**参与角色**:\n\n`;

            this.agents.forEach(agent => {
                md += `- **${agent.name}** (${agent.model}): ${agent.role}\n`;
            });

            md += `\n---\n\n`;

            let currentRound = 0;
            this.discussion.forEach(msg => {
                if (msg.round && msg.round !== currentRound) {
                    currentRound = msg.round;
                    md += `## 第 ${currentRound} 轮讨论\n\n`;
                }

                if (msg.isSummary) {
                    md += `## ✅ 最终总结\n\n`;
                }

                md += `### ${msg.speaker}\n\n`;
                md += `${msg.text}\n\n`;
                md += `---\n\n`;
            });

            return md;
        },

        // ============ UI Helpers ============
        formatMessage(text) {
            // Simple markdown-like formatting
            return text
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/`(.+?)`/g, '<code>$1</code>')
                .replace(/^(\d+)\.\s/gm, '<br>$1. ')
                .replace(/^[-*]\s/gm, '<br>• ');
        },

        scrollToBottom() {
            this.$nextTick(() => {
                const container = this.$refs.chatContainer;
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            });
        }
    }
}).mount('#app');
