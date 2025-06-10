import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'ic:baseline-view-in-ar',
      keepAlive: true,
      order: 9999,
      title: '配置中心',
    },
    name: 'ConfigCenter',
    path: '/configCenter',
    children: [
      {
        meta: {
          title: '系统配置',
        },
        name: 'Config',
        path: '/configCenter/config',
        component: () => import('#/views/configCenter/sysconfig.vue'),
      },
      {
        meta: {
          title: '通知配置',
        },
        name: 'NoticeConfig',
        path: '/configCenter/notice',
        component: () => import('#/views/configCenter/sysnotice.vue'),
      },
      {
        meta: {
          title: '资源频道设置',
        },
        name: 'ResourceChannelConfig',
        path: '/configCenter/resourceChannel',
        component: () => import('#/views/configCenter/resourceChannel.vue'),
      },
    ],
  },
];

export default routes;
