import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'ic:baseline-view-in-ar',
      // keepAlive: true,
      order: 1000,
      title: '豆瓣推荐',
    },
    name: 'Douban',
    path: '/douban',
    children: [
      {
        meta: {
          title: '热门电影',
        },
        name: 'DoubanHotMovie',
        path: '/douban/hot-movie',
        component: () => import('#/views/douban/hot-movie.vue'),
      },
      {
        meta: {
          title: '热门电视剧',
        },
        name: 'DoubanHotTv',
        path: '/douban/hot-tv',
        component: () => import('#/views/douban/hot-tv.vue'),
      },
      {
        meta: {
          title: '热门综艺',
        },
        name: 'DoubanHotZongyi',
        path: '/douban/hot-zongyi',
        component: () => import('#/views/douban/hot-zongyi.vue'),
      },
    ],
  },
];

export default routes;
