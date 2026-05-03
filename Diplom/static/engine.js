
class Engine {
    constructor(containerId, gameData, gameId) {
        this.container = document.getElementById(containerId);
        this.data      = gameData;
        this.gameId    = gameId;
        this.render();
    }
    render() {
        this.container.innerHTML = '';

        this._renderMedia();
        this._renderQuestion();

        const answerWrap = this._el('div');
        answerWrap.style.marginTop = '16px';
        answerWrap.style.width     = '100%';
        this.container.appendChild(answerWrap);

        const resultDiv = this._el('div');
        resultDiv.style.marginTop  = '14px';
        resultDiv.style.fontWeight = '600';
        resultDiv.style.fontSize   = '15px';
        this.container.appendChild(resultDiv);

        if (this.data.options && this.data.options.trim()) {
            this._renderOptions(answerWrap, resultDiv);
        } else {
            this._renderInput(answerWrap, resultDiv);
        }
    }
    _renderMedia() {
        const { type, image, audio } = this.data;

        if (type === 'image' && image) {
            const img        = this._el('img');
            img.src          = image;
            img.style.cssText = 'max-width:100%;max-height:300px;border-radius:8px;margin-bottom:20px;';
            this.container.appendChild(img);
            return;
        }

        if (type === 'audio' && audio) {
            const wrap           = this._el('div');
            wrap.style.cssText   = 'width:100%;padding:14px;background:var(--panel-alt);border:1.5px solid var(--border);border-radius:8px;margin-bottom:20px;';
            const player         = this._el('audio');
            player.controls      = true;
            player.src           = audio;
            player.style.width   = '100%';
            wrap.appendChild(player);
            this.container.appendChild(wrap);
        }
    }
    _renderQuestion() {
        const q          = this._el('h3');
        q.innerText      = this.data.question;
        q.style.cssText  = 'margin:0 0 4px;font-size:17px;text-align:center;';
        this.container.appendChild(q);
    }
    _renderOptions(wrap, resultDiv) {
        wrap.style.cssText = 'display:flex;flex-direction:column;gap:8px;width:100%;';
        this.data.options.split(';').forEach(opt => {
            const text = opt.trim();
            if (!text) return;

            const btn         = this._el('button');
            btn.innerText     = text;
            btn.style.cssText = [
                'padding:11px 16px',
                'background:var(--panel)',
                'border:1.5px solid var(--border)',
                'border-radius:8px',
                'cursor:pointer',
                'text-align:left',
                'font-size:14px',
                'font-family:inherit',
                'font-weight:500',
                'transition:border-color 0.15s,background 0.15s',
            ].join(';');

            btn.onmouseenter = () => {
                btn.style.borderColor = 'var(--primary)';
                btn.style.background  = '#f0f4ff';
            };
            btn.onmouseleave = () => {
                btn.style.borderColor = 'var(--border)';
                btn.style.background  = 'var(--panel)';
            };
            btn.onclick = () => this._check(text, wrap, resultDiv);
            wrap.appendChild(btn);
        });
    }
    _renderInput(wrap, resultDiv) {
        const input         = this._el('input');
        input.type          = 'text';
        input.placeholder   = 'Введите ответ…';
        input.style.cssText = 'width:100%;padding:10px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-family:inherit;background:var(--panel-alt);margin-bottom:8px;';
        input.onkeydown     = e => { if (e.key === 'Enter') this._check(input.value, wrap, resultDiv); };

        const btn         = this._el('button');
        btn.innerText     = 'Проверить';
        btn.className     = 'btn btn-green';
        btn.style.width   = '100%';
        btn.onclick       = () => this._check(input.value, wrap, resultDiv);

        wrap.appendChild(input);
        wrap.appendChild(btn);
    }
    _check(userAnswer, wrap, resultDiv) {
        const correct = this.data.correct_answer
            .split(';')
            .map(a => a.trim().toLowerCase());

        if (correct.includes(userAnswer.trim().toLowerCase())) {
            resultDiv.innerText     = '✅ Правильно! Молодец!';
            resultDiv.style.color   = 'var(--success)';
            wrap.querySelectorAll('button,input').forEach(el => el.disabled = true);
            this._saveProgress();
        } else {
            resultDiv.innerText   = '❌ Неверно. Попробуй ещё раз!';
            resultDiv.style.color = 'var(--danger)';
        }
    }
    _saveProgress() {
        fetch(`/progress/${this.gameId}`, { method: 'POST' })
            .then(res => {
                if (res.ok) {
                    setTimeout(() => {
                        window.location.href = `/subcategory/${this.data.subcategory_id}`;
                    }, 1400);
                }
            })
            .catch(err => console.error('Ошибка сохранения прогресса:', err));
    }
    _el(tag) { return document.createElement(tag); }
}
