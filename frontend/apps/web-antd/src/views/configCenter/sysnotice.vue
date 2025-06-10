<script setup lang="ts">
import { onActivated, onMounted } from 'vue';

import { Affix, Button, message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';

import {
  getNoticeConfigApi,
  sendNoticeMessageApi,
  updateNoticeConfigApi,
} from './api';

defineOptions({
  name: 'NoticeConfig',
});

// Form 为弹窗组件
// formApi 为弹窗的方法
const [Form, formApi] = useVbenForm({
  wrapperClass: 'm-[20px]',
  layout: 'horizontal',
  resetButtonOptions: {
    show: false,
  },
  submitButtonOptions: {
    show: false,
  },
  schema: [
    {
      component: 'Divider',
      fieldName: '',
      label: '企业微信机器人通知',
      labelWidth: 150,
      wrapperClass: 'w-full',
    },
    {
      component: 'Input',
      fieldName: 'QYWX_KEY',
      label: 'QYWX_KEY',
      labelWidth: 100,
    },
  ],
});

// 加载配置数据
const loadConfig = async () => {
  const res = await getNoticeConfigApi({});
  formApi.setFieldValue('QYWX_KEY', res.QYWX_KEY);
};

onMounted(() => {
  loadConfig();
});

onActivated(() => {
  // 当组件被缓存重新激活时，重新加载数据
  loadConfig();
});

const handleSave = async () => {
  const params = await formApi.getValues();
  await updateNoticeConfigApi(params);
  message.success('保存成功');
};

const handleSend = () => {
  sendNoticeMessageApi({
    title: '测试推送',
    content: '测试推送',
  });
  message.success('测试消息已发送');
};
</script>
<template>
  <div>
    <Form />
    <Affix :offset-bottom="50">
      <div class="mr-[20px] flex justify-end">
        <Button type="primary" @click="handleSend" class="mr-[10px]">
          测试推送
        </Button>
        <Button type="primary" @click="handleSave">保存配置</Button>
      </div>
    </Affix>
  </div>
</template>
