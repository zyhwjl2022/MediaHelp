<script setup lang="ts">
import { nextTick, onActivated, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { debouncedWatch } from '@vueuse/core';

import { Button, Form, FormItem, Input, Select } from 'ant-design-vue';

import YunpanSave from '#/views/components/yunpanSave/index.vue';

import { getResourceListApi } from './api';
import ResourceCard from './components/ResourceCard.vue';

// 定义类型接口
interface ChannelInfo {
  channelId: string;
  channelName: string;
  // 其他channelInfo字段
}

interface ResourceItem {
  id: string;
  name: string;
  cloudType: string;
  size: number;
  url: string;
  channelInfo?: ChannelInfo;
  // 其他资源字段
}

interface ApiResponse {
  channelInfo: ChannelInfo;
  list: ResourceItem[];
}

defineOptions({
  name: 'Resource',
});

const { query } = useRoute();
const loading = ref(false);
const resourceList = ref<ResourceItem[]>([]);
const allResourceList = ref<ResourceItem[]>([]);
const keyword = ref<string>(query.name as string || '');
const cloudType = ref<string>('');
const cloudTypeList = ref<{ label: string; value: string }[]>([]);
const currentItem = ref<ResourceItem | null>(null);
const open = ref(false);

// 提取公共加载逻辑
const fetchResource = async (searchKeyword?: string) => {
  try {
    loading.value = true;
    resourceList.value = [];
    
    const res = await getResourceListApi({
      keyword: searchKeyword,
    });
    
    // 平展资源列表，添加防御性编程
    const flatResourceList: ResourceItem[] = [];
    res.forEach((item: ApiResponse) => {
      const { list } = item;
      if (Array.isArray(list) && list.length > 0) {
        list.forEach((item2: ResourceItem) => {
          flatResourceList.push({
            ...(item.channelInfo || {}),
            ...item2,
            keyword: searchKeyword,
          });
        });
      }
    });
    
    // 更新云类型列表
    if (flatResourceList.length > 0) {
  cloudTypeList.value = [
    ...new Set(flatResourceList.map((item) => item.cloudType)),
  ].map((item) => ({
    label: item,
    value: item,
  }));
  
    // 新增逻辑：确保cloudType.value在cloudTypeList中存在
    if (cloudType.value) {
        const cloudTypeExists = cloudTypeList.value.some(
          (option) => option.value === cloudType.value
        );
        
        if (!cloudTypeExists && cloudTypeList.value.length > 0) {
          // 如果当前cloudType不在列表中且列表不为空，则选择第一个选项
          cloudType.value = cloudTypeList.value[0].value;
        }
        console.log('当前云类型:', cloudType.value);
      }
    } else {
      cloudTypeList.value = [];
      cloudType.value = ''; // 当资源列表为空时，清空云类型选择
    }
    
    allResourceList.value = flatResourceList;
    filterResource();
  } catch (error) {
    console.error('获取资源列表失败:', error);
    // 可以添加全局错误提示
  } finally {
    loading.value = false;
  }
};

// 过滤资源
const filterResource = () => {
  if (cloudType.value) {
    resourceList.value = allResourceList.value.filter(
      (item) => item.cloudType === cloudType.value
    );
  } else {
    cloudType.value = 'quark'; // 默认值
    resourceList.value = allResourceList.value.filter(
      (item) => item.cloudType === cloudType.value
    );
  }
};

// 保存资源处理
const onItemSave = (item: ResourceItem) => {
  currentItem.value = item;
  nextTick(() => {
    open.value = true;
  });
};

// 使用Vueuse的debouncedWatch替代lodash的debounce
debouncedWatch(cloudType, () => {
  filterResource();
}, { debounce: 300 });

// 组件挂载和激活时加载资源
const loadInitialResource = () => {
  if (keyword.value) {
    fetchResource(keyword.value.trim());
  } 
};

onMounted(loadInitialResource);
onActivated(loadInitialResource);

// 搜索资源 - 修复了undefined调用trim()的问题
const loadResource = (searchKeyword: string | undefined) => {
  // 先检查是否为字符串，再调用trim()
  const processedKeyword = searchKeyword ? searchKeyword.trim() : undefined;
  fetchResource(processedKeyword);
};
</script>

<template>
  <div v-loading="loading" class="min-h-[100vh]">
    <Form layout="inline" class="m-4" @submit.prevent="loadResource(keyword)">
      <FormItem label="关键词" name="keyword">
        <Input 
          v-model:value="keyword" 
          @keyup.enter="loadResource(keyword)" 
          placeholder="请输入关键词搜索"
        />
      </FormItem>
      <FormItem label="云类型" name="cloudType" class="w-[200px]">
        <Select
          allow-clear
          v-model:value="cloudType"
          :options="cloudTypeList"
          class="w-full"
          placeholder="请选择云类型"
        />
      </FormItem>
      <FormItem>
        <Button type="primary" @click="loadResource(keyword)">
          <i class="fa fa-search mr-2"></i>搜索
        </Button>
      </FormItem>
    </Form>
    
    <!-- 空状态处理 -->
    <div v-if="loading" class="flex justify-center items-center py-16">
      <div class="ant-spin ant-spin-lg ant-spin-spinning">
        <span class="ant-spin-dot ant-spin-dot-spin">
          <i class="ant-spin-dot-item"></i>
          <i class="ant-spin-dot-item"></i>
          <i class="ant-spin-dot-item"></i>
          <i class="ant-spin-dot-item"></i>
        </span>
      </div>
    </div>
    
    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 p-4">
      <ResourceCard
        v-for="item in resourceList"
        :key="item.id || item.name"
        :item="item"
        @save="onItemSave"
      />
      
      <!-- 空列表提示 -->
      <div 
        v-if="!loading && resourceList.length === 0" 
        class="col-span-full flex flex-col items-center justify-center py-16"
      >
        <div class="text-gray-400 text-6xl mb-4">
          <i class="fa fa-folder-open-o"></i>
        </div>
        <p class="text-gray-500 text-lg">暂无匹配的资源</p>
        <p class="text-gray-400 mt-2">请尝试使用其他关键词或云类型筛选</p>
      </div>
    </div>
    
    <YunpanSave v-model:open="open" :item="currentItem" />
  </div>
</template>

<style scoped>
/* 可以添加一些自定义样式 */
.empty-state {
  text-align: center;
  padding: 40px;
  color: #8c8c8c;
}
</style>