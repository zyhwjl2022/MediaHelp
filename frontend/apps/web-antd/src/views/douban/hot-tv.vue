<script setup lang="ts">
import { getHotMovieListApi } from './api';
import MediaCardList from './components/MediaCardList.vue';

defineOptions({
  name: 'DoubanHotTv',
});
</script>
<template>
  <div>
    <MediaCardList :api="getHotMovieListApi" :params="{ type: 'tv' }" />
  </div>
</template>
