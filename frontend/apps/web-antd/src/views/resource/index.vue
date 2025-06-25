<script setup lang="ts">
import { nextTick, onActivated, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { Button, Empty, Form, FormItem, Input, Select } from 'ant-design-vue';

import YunpanSave from '#/views/components/yunpanSave/index.vue';

import { getResourceListApi } from './api';
import ResourceCard from './components/ResourceCard.vue';

defineOptions({
  name: 'Resource',
});
const { query } = useRoute();
const loading = ref(false);
const resourceList = ref<any[]>([]);
const allResourceList = ref<any[]>([]);
const keyword = ref((query.name ?? '') as string);
const cloudType = ref('');
const cloudTypeList = ref<any[]>([]);
const currentItem = ref<any>({});
const open = ref(false);
const loadResource = async (keyword?: string) => {
  resourceList.value = [];
  loading.value = true;
  const res = await getResourceListApi({
    keyword,
  }).finally(() => {
    loading.value = false;
  });
  // 平展资源列表
  const flatResourceList: any[] = [];
  res.forEach((item: any) => {
    const { list } = item;
    if (list.length > 0) {
      list?.forEach((item2: any) => {
        flatResourceList.push({
          ...item.channelInfo,
          ...item2,
          keyword,
        });
      });
    }
  });
  cloudTypeList.value = [
    ...new Set(flatResourceList.map((item) => item.cloudType)),
  ].map((item) => ({
    label: item,
    value: item,
  }));
  allResourceList.value = flatResourceList || [];
  filterResource();
};

const filterResource = () => {
  if (cloudType.value) {
    resourceList.value = allResourceList.value.filter(
      (item) => item.cloudType === cloudType.value,
    );
    return;
  }
  resourceList.value = allResourceList.value;
};

const onItemSave = (item: any) => {
  currentItem.value = item;
  nextTick(() => {
    open.value = true;
  });
};

onMounted(() => {
  loadResource((query.name ?? '') as string);
});

onActivated(() => {
  loadResource((query.name ?? '') as string);
});
</script>

<template>
  <div v-loading="loading" class="min-h-[100vh-100px]">
    <Form layout="inline" class="m-4">
      <FormItem label="关键词" name="keyword">
        <Input v-model:value="keyword" @keyup.enter="loadResource(keyword)" />
      </FormItem>
      <FormItem label="云类型" name="cloudType" class="w-[200px]">
        <Select
          allow-clear
          v-model:value="cloudType"
          :options="cloudTypeList"
          class="w-full"
          @change="filterResource"
        />
      </FormItem>
      <FormItem>
        <Button type="primary" @click="loadResource(keyword)"> 搜索 </Button>
      </FormItem>
    </Form>
    <div
      class="grid min-h-[calc(100vh-200px)] grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
    >
      <div
        v-if="resourceList.length === 0"
        class="col-span-full flex h-full items-center justify-center"
      >
        <Empty description="暂无资源" />
      </div>
      <ResourceCard
        v-else
        v-for="item in resourceList"
        :key="item.id"
        :item="item"
        @save="onItemSave"
      />
    </div>
    <YunpanSave v-model:open="open" :item="currentItem" />
  </div>
</template>
