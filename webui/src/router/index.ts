import { createRouter, createWebHashHistory } from 'vue-router/auto';

const router = createRouter({
  history: createWebHashHistory(),
});

router.beforeEach((to) => {
  const { type, url } = storeToRefs(usePlayerStore());

  if (type.value === 'jump' && url.value !== '' && to.path === '/player') {
    open(url.value);
    return false;
  }
});

export { router };
