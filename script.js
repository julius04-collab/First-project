// DOM Elements
const form = document.getElementById('todo-form');
const input = document.getElementById('todo-input');
const todoList = document.getElementById('todo-list');
const itemsLeft = document.getElementById('items-left');
const clearCompletedBtn = document.getElementById('clear-completed');
const filterBtns = document.querySelectorAll('.filter-btn');

// State Manager
let todos = [];
let currentFilter = 'all';

// On Load
document.addEventListener('DOMContentLoaded', () => {
    loadTodos();
    renderTodos();
});

// Load from LocalStorage
function loadTodos() {
    const data = localStorage.getItem('todos');
    if (data) {
        todos = JSON.parse(data);
    }
}

// Save to LocalStorage
function saveTodos() {
    localStorage.setItem('todos', JSON.stringify(todos));
}

// Add Todo Event
form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    const newTodo = {
        id: Date.now().toString(),
        text: text,
        completed: false
    };

    todos.push(newTodo);
    saveTodos();
    input.value = '';
    
    // Switch to 'all' or 'active' filter to ensure new task is visible
    if (currentFilter === 'completed') {
        setFilter('all');
    } else {
        renderTodos();
    }
});

// Remove Todo
function removeTodo(id) {
    todos = todos.filter(todo => todo.id !== id);
    saveTodos();
    renderTodos();
}

// Toggle Todo Status
function toggleTodo(id) {
    todos = todos.map(todo => 
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
    );
    saveTodos();
    renderTodos();
}

// Clear Completed Event
clearCompletedBtn.addEventListener('click', () => {
    todos = todos.filter(todo => !todo.completed);
    saveTodos();
    renderTodos();
});

// Filter Events
filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        setFilter(btn.getAttribute('data-filter'));
    });
});

function setFilter(filter) {
    currentFilter = filter;
    
    // Update active UI
    filterBtns.forEach(btn => {
        if (btn.getAttribute('data-filter') === filter) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    renderTodos();
}

// Render the list
function renderTodos() {
    todoList.innerHTML = '';

    // Calculate remaining items
    const activeTodos = todos.filter(todo => !todo.completed);
    itemsLeft.innerText = `${activeTodos.length} item${activeTodos.length !== 1 ? 's' : ''} left`;

    // Toggle clear completed button
    const hasCompleted = todos.some(todo => todo.completed);
    clearCompletedBtn.style.display = hasCompleted ? 'inline-block' : 'none';

    // Apply Filters
    let displayTodos = todos;
    if (currentFilter === 'active') {
        displayTodos = activeTodos;
    } else if (currentFilter === 'completed') {
        displayTodos = todos.filter(todo => todo.completed);
    }

    if (displayTodos.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerText = currentFilter === 'all' 
            ? "No tasks yet. Add one above!" 
            : `No ${currentFilter} tasks.`;
        todoList.appendChild(emptyState);
        return;
    }

    // Build DOM elements
    displayTodos.forEach(todo => {
        const li = document.createElement('li');
        li.className = `todo-item ${todo.completed ? 'completed' : ''}`;
        li.dataset.id = todo.id;

        const label = document.createElement('label');
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'checkbox';
        checkbox.checked = todo.completed;
        checkbox.addEventListener('change', () => toggleTodo(todo.id));

        const customCheck = document.createElement('span');
        customCheck.className = 'custom-checkbox';
        const icon = document.createElement('i');
        icon.className = 'fas fa-check';
        customCheck.appendChild(icon);

        label.appendChild(checkbox);
        label.appendChild(customCheck);

        const span = document.createElement('span');
        span.className = 'todo-text';
        span.innerText = todo.text;

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
        deleteBtn.addEventListener('click', () => {
            li.classList.add('fade-out');
            setTimeout(() => {
                removeTodo(todo.id);
            }, 250); // Matches CSS animation duration
        });

        li.appendChild(label);
        li.appendChild(span);
        li.appendChild(deleteBtn);

        todoList.appendChild(li);
    });
}
