// 通用底部抽屉 UI 组件 (Reusable Self-contained Bottom Sheet Component)
import { refreshIcons } from '../utils/dom.js';

export class BottomSheet {
    constructor(options = {}) {
        this.id = options.id || `sheet_${Math.random().toString(36).substring(2, 9)}`;
        this.title = options.title || '';
        this.subtitle = options.subtitle || '';
        this.icon = options.icon || 'layers';
        this.maxHeight = options.maxHeight || '85vh';
        this.renderBody = options.renderBody || (() => '');
        this.onOpen = options.onOpen || null;
        this.onClose = options.onClose || null;

        this.backdropEl = null;
        this.sheetEl = null;
        this.bodyEl = null;
        this.isOpen = false;

        this._initDOM();
    }

    _initDOM() {
        // 1. 创建背景遮罩
        this.backdropEl = document.createElement('div');
        this.backdropEl.className = 'sheet-backdrop';
        this.backdropEl.id = `${this.id}Backdrop`;
        this.backdropEl.addEventListener('click', () => this.close());

        // 2. 创建抽屉容器
        this.sheetEl = document.createElement('div');
        this.sheetEl.className = 'mobile-bottom-sheet';
        this.sheetEl.id = this.id;
        this.sheetEl.style.maxHeight = this.maxHeight;

        this.sheetEl.innerHTML = `
            <div class="sheet-handle-bar"></div>
            <div class="sheet-header">
                <div class="sheet-title-wrap">
                    <i data-lucide="${this.icon}" style="width: 18px; height: 18px; color: var(--primary);"></i>
                    <span class="sheet-title">${this.title}</span>
                </div>
                <button class="sheet-close-icon" type="button" aria-label="关闭">
                    <i data-lucide="x" style="width: 16px; height: 16px;"></i>
                </button>
            </div>
            ${this.subtitle ? `<div class="sheet-subtitle">${this.subtitle}</div>` : ''}
            <div class="sheet-scroll-body" id="${this.id}Body" style="flex: 1; overflow-y: auto; padding: 12px 16px;"></div>
        `;

        // 绑定手柄与关闭按钮事件
        this.sheetEl.querySelector('.sheet-handle-bar').addEventListener('click', () => this.close());
        this.sheetEl.querySelector('.sheet-close-icon').addEventListener('click', () => this.close());

        this.bodyEl = this.sheetEl.querySelector(`#${this.id}Body`);

        // 挂载到 body 尾部
        document.body.appendChild(this.backdropEl);
        document.body.appendChild(this.sheetEl);

        // 渲染初态内容
        this.updateBody();
    }

    updateBody(customHtml = null) {
        if (!this.bodyEl) return;
        if (customHtml !== null) {
            this.bodyEl.innerHTML = customHtml;
        } else if (typeof this.renderBody === 'function') {
            this.bodyEl.innerHTML = this.renderBody();
        }
        refreshIcons();
    }

    open() {
        this.isOpen = true;
        this.backdropEl.classList.add('active');
        this.sheetEl.classList.add('active');
        document.body.style.overflow = 'hidden';

        if (typeof this.onOpen === 'function') {
            this.onOpen(this);
        }
        refreshIcons();
    }

    close() {
        this.isOpen = false;
        this.backdropEl.classList.remove('active');
        this.sheetEl.classList.remove('active');
        document.body.style.overflow = '';

        if (typeof this.onClose === 'function') {
            this.onClose(this);
        }
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    destroy() {
        if (this.backdropEl) this.backdropEl.remove();
        if (this.sheetEl) this.sheetEl.remove();
    }
}
