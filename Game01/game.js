// 제비우스 스타일 종스크롤 슈팅게임
(() => {
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;

  const scoreEl = document.getElementById('score');
  const livesEl = document.getElementById('lives');
  const overlay = document.getElementById('overlay');
  const overlayTitle = document.getElementById('overlay-title');
  const overlayDesc = document.getElementById('overlay-desc');

  const keys = {};
  window.addEventListener('keydown', (e) => {
    keys[e.code] = true;
    if (e.code === 'Space' && (gameOver || !started)) startGame();
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
  });
  window.addEventListener('keyup', (e) => { keys[e.code] = false; });

  // ---------- 사운드 효과 (Web Audio 합성) ----------
  const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
  const audioCtx = AudioCtxClass ? new AudioCtxClass() : null;
  function unlockAudio() {
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  }
  window.addEventListener('keydown', unlockAudio, { once: true });

  function playTone({ freq = 440, duration = 0.1, type = 'square', volume = 0.15, slideTo = null }) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    if (slideTo !== null) {
      osc.frequency.exponentialRampToValueAtTime(Math.max(slideTo, 1), audioCtx.currentTime + duration);
    }
    gain.gain.setValueAtTime(volume, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  }

  const sfx = {
    shoot: () => playTone({ freq: 900, duration: 0.08, type: 'square', volume: 0.08, slideTo: 500 }),
    bomb: () => playTone({ freq: 300, duration: 0.15, type: 'sawtooth', volume: 0.12, slideTo: 120 }),
    explosion: () => playTone({ freq: 220, duration: 0.25, type: 'triangle', volume: 0.2, slideTo: 40 }),
    hit: () => playTone({ freq: 150, duration: 0.3, type: 'sawtooth', volume: 0.25, slideTo: 30 }),
    gameover: () => playTone({ freq: 200, duration: 0.6, type: 'sawtooth', volume: 0.25, slideTo: 20 }),
  };

  // ---------- 지형(스크롤 배경) ----------
  const terrainTiles = [];
  const TILE_H = 80;
  function genTerrainRow(y) {
    const row = { y, items: [] };
    const rand = Math.random();
    if (rand < 0.35) {
      row.items.push({ type: 'river', x: 60 + Math.random() * (W - 180), w: 100 + Math.random() * 60 });
    } else if (rand < 0.6) {
      row.items.push({ type: 'patch', x: Math.random() * W, w: 40 + Math.random() * 50 });
    }
    return row;
  }
  for (let y = -TILE_H; y < H + TILE_H; y += TILE_H) {
    terrainTiles.push(genTerrainRow(y));
  }
  let terrainScroll = 0;
  const scrollSpeed = 1.6;

  function updateTerrain() {
    terrainScroll += scrollSpeed;
    terrainTiles.forEach((row) => { row.y += scrollSpeed; });
    if (terrainTiles[0].y > H) {
      terrainTiles.shift();
      const last = terrainTiles[terrainTiles.length - 1];
      terrainTiles.push(genTerrainRow(last.y - TILE_H));
    }
  }

  function drawTerrain() {
    ctx.fillStyle = '#123a12';
    ctx.fillRect(0, 0, W, H);
    terrainTiles.forEach((row) => {
      row.items.forEach((item) => {
        if (item.type === 'river') {
          ctx.fillStyle = '#1b4d7a';
          ctx.fillRect(item.x, row.y, item.w, TILE_H * 0.7);
        } else {
          ctx.fillStyle = '#1e5c1e';
          ctx.fillRect(item.x, row.y, item.w, item.w);
        }
      });
    });
  }

  // ---------- 지상 목표물(폭격 대상) ----------
  let groundTargets = [];
  function spawnGroundTarget() {
    groundTargets.push({
      x: 30 + Math.random() * (W - 60),
      y: -20,
      w: 26,
      h: 26,
      destroyed: false,
      score: 150,
    });
  }
  let groundSpawnTimer = 0;

  // ---------- 공중 적 ----------
  let enemies = [];
  const FRUITS = [
    { name: 'apple', body: '#ff3b3b', accent: '#7a1f1f', leaf: '#3ecb3e', pattern: 'straight', score: 100 },
    { name: 'cherry', body: '#c81e5c', accent: '#7a0f38', leaf: '#3ecb3e', pattern: 'weave', score: 120 },
    { name: 'orange', body: '#ff9a1f', accent: '#b35e00', leaf: '#3ecb3e', pattern: 'straight', score: 110 },
    { name: 'grape', body: '#8e4bd1', accent: '#4c2273', leaf: '#3ecb3e', pattern: 'weave', score: 130 },
  ];
  function spawnEnemy() {
    const fruit = FRUITS[Math.floor(Math.random() * FRUITS.length)];
    enemies.push({
      fruit,
      x: 30 + Math.random() * (W - 60),
      y: -20,
      w: 24,
      h: 24,
      vx: fruit.pattern === 'weave' ? (Math.random() < 0.5 ? -1 : 1) * 1.5 : 0,
      vy: 1.2 + Math.random() * 0.8,
      t: 0,
      hp: 1,
      score: fruit.score,
      fireCooldown: 60 + Math.random() * 60,
    });
  }
  let enemySpawnTimer = 0;

  // ---------- 플레이어 ----------
  const player = {
    x: W / 2,
    y: H - 100,
    w: 24,
    h: 28,
    speed: 4,
    cooldownAir: 0,
    cooldownBomb: 0,
    alive: true,
    invincible: 0,
  };

  let airBullets = [];
  let bombs = [];
  let enemyBullets = [];
  let explosions = [];

  let score = 0;
  let lives = 3;
  let gameOver = false;
  let started = false;
  let frame = 0;

  function resetGame() {
    groundTargets = [];
    enemies = [];
    airBullets = [];
    bombs = [];
    enemyBullets = [];
    explosions = [];
    score = 0;
    lives = 3;
    gameOver = false;
    frame = 0;
    player.x = W / 2;
    player.y = H - 100;
    player.alive = true;
    player.invincible = 120;
    updateHud();
  }

  function startGame() {
    resetGame();
    started = true;
    overlay.classList.add('hidden');
  }

  function updateHud() {
    scoreEl.textContent = `SCORE: ${score}`;
    livesEl.textContent = `LIVES: ${lives}`;
  }

  function rectsOverlap(a, b) {
    return (
      a.x - a.w / 2 < b.x + b.w / 2 &&
      a.x + a.w / 2 > b.x - b.w / 2 &&
      a.y - a.h / 2 < b.y + b.h / 2 &&
      a.y + a.h / 2 > b.y - b.h / 2
    );
  }

  function addExplosion(x, y, size = 24) {
    explosions.push({ x, y, r: 4, maxR: size, alpha: 1 });
  }

  // ---------- 입력/플레이어 업데이트 ----------
  function updatePlayer() {
    if (!player.alive) return;
    if (keys['ArrowLeft']) player.x -= player.speed;
    if (keys['ArrowRight']) player.x += player.speed;
    if (keys['ArrowUp']) player.y -= player.speed;
    if (keys['ArrowDown']) player.y += player.speed;
    player.x = Math.max(player.w / 2, Math.min(W - player.w / 2, player.x));
    player.y = Math.max(player.h / 2, Math.min(H - player.h / 2, player.y));

    if (player.cooldownAir > 0) player.cooldownAir--;
    if (player.cooldownBomb > 0) player.cooldownBomb--;

    if (keys['KeyZ'] && player.cooldownAir === 0) {
      airBullets.push({ x: player.x, y: player.y - player.h / 2, w: 4, h: 10, vy: -8 });
      player.cooldownAir = 10;
      sfx.shoot();
    }
    if (keys['KeyX'] && player.cooldownBomb === 0) {
      bombs.push({
        x: player.x,
        y: player.y,
        w: 6,
        h: 6,
        vy: -2,
        targetY: player.y - 140,
        exploded: false,
      });
      player.cooldownBomb = 30;
      sfx.bomb();
    }
    if (player.invincible > 0) player.invincible--;
  }

  // ---------- 탄/폭탄 업데이트 ----------
  function updateBullets() {
    airBullets.forEach((b) => { b.y += b.vy; });
    airBullets = airBullets.filter((b) => b.y > -20);

    bombs.forEach((b) => {
      b.y += b.vy;
      b.vy += 0.05; // 서서히 감속 후 낙하 지점 도달
      if (b.y <= b.targetY) b.exploded = true;
    });
    bombs = bombs.filter((b) => !b.exploded && b.y > -20);

    enemyBullets.forEach((b) => { b.x += b.vx; b.y += b.vy; });
    enemyBullets = enemyBullets.filter((b) => b.y < H + 20 && b.y > -20 && b.x > -20 && b.x < W + 20);
  }

  // ---------- 지상 목표물 업데이트 ----------
  function updateGroundTargets() {
    groundSpawnTimer--;
    if (groundSpawnTimer <= 0) {
      spawnGroundTarget();
      groundSpawnTimer = 70 + Math.random() * 50;
    }
    groundTargets.forEach((g) => { g.y += scrollSpeed; });
    groundTargets = groundTargets.filter((g) => !g.destroyed && g.y < H + 40);
  }

  // ---------- 공중 적 업데이트 ----------
  function updateEnemies() {
    enemySpawnTimer--;
    if (enemySpawnTimer <= 0) {
      spawnEnemy();
      enemySpawnTimer = 60 + Math.random() * 60;
    }
    enemies.forEach((e) => {
      e.t += 1;
      e.y += e.vy;
      if (e.fruit.pattern === 'weave') e.x += Math.sin(e.t * 0.05) * 2;
      else e.x += e.vx;

      e.fireCooldown--;
      if (e.fireCooldown <= 0 && e.y > 0 && e.y < H - 60 && player.alive) {
        const dx = player.x - e.x;
        const dy = player.y - e.y;
        const dist = Math.hypot(dx, dy) || 1;
        enemyBullets.push({ x: e.x, y: e.y, w: 5, h: 5, vx: (dx / dist) * 3, vy: (dy / dist) * 3 });
        e.fireCooldown = 90 + Math.random() * 60;
      }
    });
    enemies = enemies.filter((e) => e.y < H + 40 && e.hp > 0);
  }

  // ---------- 충돌 판정 ----------
  function checkCollisions() {
    // 공중 탄 vs 공중 적
    airBullets.forEach((b) => {
      enemies.forEach((e) => {
        if (e.hp > 0 && rectsOverlap({ x: b.x, y: b.y, w: b.w, h: b.h }, e)) {
          e.hp -= 1;
          b.y = -999;
          if (e.hp <= 0) {
            score += e.score;
            addExplosion(e.x, e.y);
            sfx.explosion();
            updateHud();
          }
        }
      });
    });

    // 폭탄 폭발 vs 지상 목표물
    bombs.forEach((b) => {
      if (b.exploded) {
        groundTargets.forEach((g) => {
          if (!g.destroyed && Math.hypot(g.x - b.x, g.y - b.y) < 28) {
            g.destroyed = true;
            score += g.score;
            addExplosion(g.x, g.y, 30);
            sfx.explosion();
            updateHud();
          }
        });
      }
    });

    if (player.alive && player.invincible <= 0) {
      const pRect = player;
      const hitByEnemy = enemies.some((e) => rectsOverlap(pRect, e));
      const hitByBullet = enemyBullets.some((b) => rectsOverlap(pRect, { x: b.x, y: b.y, w: b.w, h: b.h }));
      if (hitByEnemy || hitByBullet) {
        killPlayer();
      }
    }
  }

  function killPlayer() {
    addExplosion(player.x, player.y, 36);
    sfx.hit();
    lives -= 1;
    updateHud();
    if (lives <= 0) {
      player.alive = false;
      endGame();
    } else {
      player.x = W / 2;
      player.y = H - 100;
      player.invincible = 120;
    }
  }

  function endGame() {
    gameOver = true;
    started = false;
    overlayTitle.textContent = 'GAME OVER';
    overlayDesc.textContent = `SCORE ${score} - 스페이스바를 눌러 재시작`;
    overlay.classList.remove('hidden');
    sfx.gameover();
  }

  function updateExplosions() {
    explosions.forEach((ex) => {
      ex.r += 2;
      ex.alpha -= 0.05;
    });
    explosions = explosions.filter((ex) => ex.alpha > 0);
  }

  // ---------- 렌더링 ----------
  function drawPlayer() {
    if (!player.alive) return;
    if (player.invincible > 0 && Math.floor(frame / 4) % 2 === 0) return;
    const flicker = Math.floor(frame / 3) % 2 === 0;
    ctx.save();
    ctx.translate(player.x, player.y);

    // 엔진 불깃
    ctx.fillStyle = flicker ? '#ffcc33' : '#ff9933';
    ctx.beginPath();
    ctx.moveTo(-6, player.h / 2 - 2);
    ctx.lineTo(0, player.h / 2 + 10);
    ctx.lineTo(6, player.h / 2 - 2);
    ctx.closePath();
    ctx.fill();

    // 뒤즤 날개(허)
    ctx.fillStyle = '#2a6fb0';
    ctx.beginPath();
    ctx.moveTo(-player.w / 2 - 6, player.h / 2);
    ctx.lineTo(-6, player.h / 4);
    ctx.lineTo(-6, player.h / 2);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(player.w / 2 + 6, player.h / 2);
    ctx.lineTo(6, player.h / 4);
    ctx.lineTo(6, player.h / 2);
    ctx.closePath();
    ctx.fill();

    // 메인 동체(그라디언트 느낌)
    const grad = ctx.createLinearGradient(0, -player.h / 2, 0, player.h / 2);
    grad.addColorStop(0, '#f2fbff');
    grad.addColorStop(1, '#7fb8e0');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.moveTo(0, -player.h / 2 - 4);
    ctx.lineTo(player.w / 2, player.h / 3);
    ctx.lineTo(player.w / 4, player.h / 2);
    ctx.lineTo(-player.w / 4, player.h / 2);
    ctx.lineTo(-player.w / 2, player.h / 3);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = '#1c4f78';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 주날개
    ctx.fillStyle = '#3aa8ff';
    ctx.beginPath();
    ctx.moveTo(0, -6);
    ctx.lineTo(player.w / 2 + 6, player.h / 3);
    ctx.lineTo(6, player.h / 3);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(0, -6);
    ctx.lineTo(-player.w / 2 - 6, player.h / 3);
    ctx.lineTo(-6, player.h / 3);
    ctx.closePath();
    ctx.fill();

    // 조종석(켵핑)
    ctx.fillStyle = '#0d2b40';
    ctx.beginPath();
    ctx.ellipse(0, -player.h / 6, 4, 7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#7fe8ff';
    ctx.beginPath();
    ctx.ellipse(0, -player.h / 6 - 1, 2.2, 3.5, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  function drawBullets() {
    ctx.fillStyle = '#ffff66';
    airBullets.forEach((b) => ctx.fillRect(b.x - b.w / 2, b.y - b.h / 2, b.w, b.h));

    ctx.fillStyle = '#ff8844';
    bombs.forEach((b) => {
      ctx.beginPath();
      ctx.arc(b.x, b.y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    ctx.fillStyle = '#ff3366';
    enemyBullets.forEach((b) => {
      ctx.beginPath();
      ctx.arc(b.x, b.y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function drawGroundTargets() {
    groundTargets.forEach((g) => {
      ctx.fillStyle = '#553311';
      ctx.fillRect(g.x - g.w / 2, g.y - g.h / 2, g.w, g.h);
      ctx.strokeStyle = '#ffaa00';
      ctx.strokeRect(g.x - g.w / 2, g.y - g.h / 2, g.w, g.h);
    });
  }

  function drawEnemies() {
    enemies.forEach((e) => {
      const f = e.fruit;
      ctx.save();
      ctx.translate(e.x, e.y);

      // 잎사귀
      ctx.strokeStyle = '#5a3a1a';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, -e.w / 2);
      ctx.lineTo(2, -e.w / 2 - 6);
      ctx.stroke();

      // 잎
      ctx.fillStyle = f.leaf;
      ctx.beginPath();
      ctx.ellipse(5, -e.w / 2 - 6, 5, 3, Math.PI / 4, 0, Math.PI * 2);
      ctx.fill();

      // 과일 몸통
      const grad = ctx.createRadialGradient(-e.w / 6, -e.w / 6, 2, 0, 0, e.w / 2);
      grad.addColorStop(0, '#ffffff');
      grad.addColorStop(0.25, f.body);
      grad.addColorStop(1, f.accent);
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(0, 0, e.w / 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = f.accent;
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.restore();
    });
  }

  function drawExplosions() {
    explosions.forEach((ex) => {
      ctx.save();
      ctx.globalAlpha = Math.max(ex.alpha, 0);
      ctx.strokeStyle = '#ffdd55';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(ex.x, ex.y, ex.r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    });
  }

  function drawBombTargetReticle() {
    if (!player.alive) return;
    ctx.strokeStyle = 'rgba(255,255,255,0.5)';
    ctx.strokeRect(player.x - 10, player.y - 150, 20, 20);
  }

  function render() {
    drawTerrain();
    drawGroundTargets();
    drawBombTargetReticle();
    drawEnemies();
    drawBullets();
    drawExplosions();
    drawPlayer();
  }

  // ---------- 메인 루프 ----------
  function loop() {
    frame++;
    if (started && !gameOver) {
      updateTerrain();
      updatePlayer();
      updateBullets();
      updateGroundTargets();
      updateEnemies();
      checkCollisions();
      updateExplosions();
    } else {
      updateExplosions();
    }
    render();
    requestAnimationFrame(loop);
  }

  overlayTitle.textContent = '제비우스 종스크롤 슈팅';
  overlayDesc.textContent = '스페이스바를 눌러 시작';
  overlay.classList.remove('hidden');
  updateHud();
  render();
  requestAnimationFrame(loop);
})();
