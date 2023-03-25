class CustomComboBox extends HTMLElement {
    constructor() {
        super();
        const optionsString = this.getAttribute('options') || '';
        this.options = optionsString.split(',').map(option => option.trim()).filter(option => option !== '');
        // this.options = this.getAttribute('options') ? JSON.parse(this.getAttribute('options')) : [];
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
      <style>
        .input {
          display: inline-block;
          position: relative;
        }
        .suggestions {
          position: absolute;
          top: 100%;
          left: 0;
          width: 100%;
          z-index: 1;
          border: 1px solid gray;
          background-color: white;
          max-height: 150px;
          overflow-y: auto;
        }
        .suggestion {
          padding: 5px;
          cursor: pointer;
        }
        .highlighted {
          background-color: #4CAF50;
          color: white;
        }
      </style>
      <div class="input">
        <input type="text">
        <div class="suggestions"></div>
      </div>
    `;
        this.input = this.shadowRoot.querySelector('input');
        this.suggestions = this.shadowRoot.querySelector('.suggestions');
        this.highlightedIndex = -1;
        this.filteredOptions = [...this.options];
    }

    connectedCallback() {
        this.input.addEventListener('input', e => {
            const value = e.target.value;
            this.filterOptions(value);
            this.renderSuggestions();
        });

        this.input.addEventListener('keydown', e => {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.highlightPrevious();
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.highlightNext();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                this.selectHighlighted();
            }
        });

        this.suggestions.addEventListener('mousedown', e => {
            const index = parseInt(e.target.dataset.index);
            this.highlightOption(index);
            this.selectOption(index);
        });

        this.suggestions.addEventListener('mouseover', e => {
            const index = parseInt(e.target.dataset.index);
            this.highlightOption(index);
        });
    }

    filterOptions(value) {
        this.filteredOptions = this.options.filter(option =>
            option.toLowerCase().includes(value.toLowerCase())
        );
        this.highlightedIndex = -1;
    }

    renderSuggestions() {
        this.suggestions.innerHTML = '';
        this.filteredOptions.forEach((option, index) => {
            const div = document.createElement('div');
            const isSelected = this.highlightedIndex === index;
            div.classList.add('suggestion');
            if (isSelected) {
                div.classList.add('highlighted');
            }
            div.innerText = option;
            div.dataset.index = index;
            this.suggestions.appendChild(div);
        });
    }

    highlightOption(index) {
        if (!isNaN(index)) {
            const suggestions = this.suggestions.querySelectorAll('.suggestion');
            suggestions.forEach(suggestion => suggestion.classList.remove('highlighted'));
            this.highlightedIndex = index;
            suggestions[index].classList.add('highlighted');
        }
    }

    highlightNext() {
        if (this.highlightedIndex >= this.filteredOptions.length - 1) {
            this.highlightOption(0);
        } else {
            this.highlightOption(this.highlightedIndex + 1);
        }
    }

    highlightPrevious() {
        if (this.highlightedIndex <= 0) {
            this.highlightOption(this.filteredOptions.length - 1);
        } else {
            this.highlightOption(this.highlightedIndex - 1);
        }
    }

    selectHighlighted() {
        if (this.highlightedIndex !== -1) {
            this.selectOption(this.highlightedIndex);
        }
    }

    selectOption(index) {
        const selectedOption = this.filteredOptions[index];
        this.input.value = selectedOption;
        this.closeSuggestions();
    }

    closeSuggestions() {
        this.suggestions.innerHTML = '';
    }
}

customElements.define('custom-combo-box', CustomComboBox);