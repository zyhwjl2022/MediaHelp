<script setup lang="ts">
import { useVbenForm } from '#/adapter/form';
// Form 为弹窗组件
// formApi 为弹窗的方法
const [Form] = useVbenForm({
  wrapperClass: 'm-[20px]',
  layout: 'horizontal',
  resetButtonOptions: {
    show: false,
  },
  submitButtonOptions: {
    show: true,
    content: '保存配置',
  },
  schema: [
    {
      component: 'Divider',
      fieldName: '',
      label: 'Emby配置',
      labelWidth: 80,
      wrapperClass: 'w-full',
    },
    {
      component: 'Input',
      fieldName: 'emby_url',
      label: 'Emby地址',
      labelWidth: 100,
    },
    {
      component: 'Input',
      fieldName: 'emby_api_key',
      label: 'Emby APi秘钥',
      labelWidth: 100,
    },
    {
      component: 'Divider',
      fieldName: '',
      label: 'Alist配置',
      labelWidth: 80,
      wrapperClass: 'w-full',
    },
    {
      component: 'Input',
      fieldName: 'alist_url',
      label: 'Alist地址',
      labelWidth: 100,
    },
    {
      component: 'Input',
      fieldName: 'alist_api_key',
      label: 'Alist APi秘钥',
      labelWidth: 100,
    },
    {
      component: 'Divider',
      fieldName: '',
      label: '天翼云盘配置',
      labelWidth: 90,
      wrapperClass: 'w-full',
    },
    {
      component: 'Input',
      fieldName: 'tianyiAccount',
      label: '天翼云盘账号',
      labelWidth: 100,
    },
    {
      component: 'Input',
      fieldName: 'tianyiPassword',
      label: '天翼云盘密码',
      labelWidth: 100,
    },
    {
      component: 'Divider',
      fieldName: '',
      label: '夸克云盘配置',
      labelWidth: 100,
    },
    {
      component: 'Input',
      fieldName: 'quarkCookie',
      label: '夸克云盘Cookie',
      labelWidth: 100,
    },
  ],
});
</script>
<template>
  <Form />
</template>
