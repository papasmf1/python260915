const STORAGE_KEY = 'todo-list-items';

let todos = [];
let currentFilter = 'all';

const todoForm = document.querySelector('#todo-form');
const todoInput = document.querySelector('#todo-input');
const todoList = document.querySelector('#todo-list');
const formMessage = document.querySelector('#form-message');
const listSummary = document.querySelector('#list-summary');
const visibleCount = document.querySelector('#visible-count');
const remainingCount = document.querySelector('#remaining-count');
const completedCount = document.querySelector('#completed-count');
const filterButtons = document.querySelectorAll('[data-filter]');

function init() {
  todos = loadTodos();
  todoForm.addEventListener('submit', handleAddTodo);
  todoList.addEventListener('change', handleTodoChange);
  todoList.addEventListener('click', handleTodoClick);
  filterButtons.forEach((button) => {
    button.addEventListener('click', () => handleFilterChange(button.dataset.filter));
  });
  render();
}

function handleAddTodo(event) {
  event.preventDefault();
  const text = todoInput.value.trim();

  if (!text) {
    showMessage('할 일 내용을 입력해주세요.');
    todoInput.focus();
    return;
  }

  todos.unshift({
    id: createId(),
    text,
    completed: false,
    createdAt: new Date().toISOString(),
  });

  saveTodos();
  todoForm.reset();
  showMessage('할 일이 추가되었습니다.');
  todoInput.focus();
  render();
}

function handleTodoChange(event) {
  if (!event.target.matches('[data-action="toggle"]')) {
    return;
  }

  const todoItem = event.target.closest('[data-todo-id]');
  if (!todoItem) {
    return;
  }

  handleToggleTodo(todoItem.dataset.todoId);
}

function handleTodoClick(event) {
  const deleteButton = event.target.closest('[data-action="delete"]');
  if (!deleteButton) {
    return;
  }

  const todoItem = deleteButton.closest('[data-todo-id]');
  if (!todoItem) {
    return;
  }

  handleDeleteTodo(todoItem.dataset.todoId);
}

function handleToggleTodo(id) {
  todos = todos.map((todo) => (
    todo.id === id ? { ...todo, completed: !todo.completed } : todo
  ));
  saveTodos();
  render();
}

function handleDeleteTodo(id) {
  todos = todos.filter((todo) => todo.id !== id);
  saveTodos();
  showMessage('할 일이 삭제되었습니다.');
  render();
}

function handleFilterChange(filter) {
  currentFilter = filter;
  filterButtons.forEach((button) => {
    const isActive = button.dataset.filter === currentFilter;
    button.classList.toggle('is-active', isActive);
    button.setAttribute('aria-pressed', String(isActive));
  });
  render();
}

function render() {
  const filteredTodos = getFilteredTodos();
  const remainingTodos = todos.filter((todo) => !todo.completed);
  const completedTodos = todos.filter((todo) => todo.completed);

  todoList.replaceChildren();

  if (filteredTodos.length === 0) {
    todoList.append(createEmptyState());
  } else {
    filteredTodos.forEach((todo) => todoList.append(createTodoElement(todo)));
  }

  visibleCount.textContent = `${filteredTodos.length}개`;
  remainingCount.textContent = `${remainingTodos.length}개 남음`;
  completedCount.textContent = `${completedTodos.length}개 완료`;
  listSummary.textContent = todos.length === 0
    ? '작은 한 걸음부터 오늘을 정리해보세요.'
    : `전체 ${todos.length}개 중 ${remainingTodos.length}개가 진행 중입니다.`;
}

function createTodoElement(todo) {
  const item = document.createElement('li');
  item.className = `todo-item${todo.completed ? ' is-completed' : ''}`;
  item.dataset.todoId = todo.id;

  const checkLabel = document.createElement('label');
  checkLabel.className = 'todo-check';
  checkLabel.title = todo.completed ? '미완료로 표시' : '완료로 표시';

  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.checked = todo.completed;
  checkbox.dataset.action = 'toggle';
  checkbox.setAttribute('aria-label', `${todo.text} 완료 상태 변경`);

  const checkText = document.createElement('span');
  checkText.className = 'sr-only';
  checkText.textContent = todo.completed ? '완료됨' : '미완료';

  checkLabel.append(checkbox, checkText);

  const text = document.createElement('span');
  text.className = 'todo-text';
  text.textContent = todo.text;

  const deleteButton = document.createElement('button');
  deleteButton.type = 'button';
  deleteButton.className = 'delete-button';
  deleteButton.dataset.action = 'delete';
  deleteButton.setAttribute('aria-label', `${todo.text} 삭제`);
  deleteButton.textContent = '삭제';

  item.append(checkLabel, text, deleteButton);
  return item;
}

function createEmptyState() {
  const emptyState = document.createElement('li');
  emptyState.className = 'empty-state';
  emptyState.textContent = currentFilter === 'all'
    ? '아직 등록된 할 일이 없습니다.'
    : currentFilter === 'active'
      ? '진행 중인 할 일이 없습니다.'
      : '완료된 할 일이 없습니다.';
  return emptyState;
}

function getFilteredTodos() {
  if (currentFilter === 'active') {
    return todos.filter((todo) => !todo.completed);
  }
  if (currentFilter === 'completed') {
    return todos.filter((todo) => todo.completed);
  }
  return todos;
}

function saveTodos() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
  } catch (error) {
    showMessage('저장할 수 없어 현재 화면에만 반영되었습니다.');
  }
}

function loadTodos() {
  try {
    const savedTodos = localStorage.getItem(STORAGE_KEY);
    if (!savedTodos) {
      return [];
    }

    const parsedTodos = JSON.parse(savedTodos);
    return Array.isArray(parsedTodos) ? parsedTodos : [];
  } catch (error) {
    return [];
  }
}

function createId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function showMessage(message) {
  formMessage.textContent = message;
  window.clearTimeout(showMessage.timeoutId);
  showMessage.timeoutId = window.setTimeout(() => {
    formMessage.textContent = '';
  }, 2600);
}

init();
