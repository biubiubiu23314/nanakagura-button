<template>
    <div class="container-fluid">
            <div>
                <div class="cate-header">{{ $t("action.control")}}</div>
                <div class="cate-body"><button class="btn btn-info" @click="stopPlay">{{$t("action.stopvoice")}}</button></div>
                <audio id="player"></audio>
            </div>
        <div v-for="category in voices" v-bind:key="category.categoryName">
            <div v-if="needToShow(category.categoryDescription)" class="cate-header">{{ $t("voicecategory." + category.categoryName) }}</div>
            <div class="cate-body">
                <button v-if="needToShow(voiceItem.description) && !usePicture(voiceItem)" class="btn btn-new" v-for="voiceItem in category.voiceList" v-bind:key="voiceItem.name" @click="play(category.categoryName+ '/' + voiceItem.path)">
                    {{ $t("voice." + voiceItem.name )}}
                </button>
                <vue-responsive-image 
                    v-if="needToShow(voiceItem.description) && usePicture(voiceItem)" 
                    v-for="voiceItem in category.voiceList" 
                    v-bind:key="voiceItem.name" 
                    class="meme-image"
                    :image-url="getPicture(voiceItem)" 
                    :width-on-screen="8"
                    :width-on-screen-tablet="10"
                    :width-on-screen-smartphone="15"
                    @click.native="play(category.categoryName+ '/' + voiceItem.path)"
                    >
                </vue-responsive-image>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.cate-header{
    background-color: rgba(255, 0, 0, 0.712);
    border: 1px solid rgba(0, 0, 0, 0.5);
    border-radius: 10px;
    text-align: center;
    font-size: 20px;
    margin-bottom: 12px;
}
.cate-body{
    margin-bottom: 12px;
    text-align: center;
}
.cate-body button{
    margin: 5px;
}
.btn-new {
    color: #fff;
    background-color: rgb(120, 140, 160);//按钮背景颜色
    border-color: rgb(207, 135, 207);//按钮框颜色
}

.meme-image img {
    transition: .2s
}

.meme-image:hover img {
    transform: scale(2.0)
}

</style>


<script>
import Vue from 'vue'
import Component from 'vue-class-component'
import VoiceList from '../nanakagura_voices.json'
import VueResponsiveImage from 'vue-responsive-image'

Vue.component('vue-responsive-image', VueResponsiveImage);

@Component
class HomePage extends Vue {
    voices = VoiceList.voices
    scaled = false
    play(path){
        this.stopPlay();
        let player = document.getElementById('player');
        player.src = "voices/" + path;
        player.play();
    }
    stopPlay(){
        let player = document.getElementById('player');
        player.pause();
    }
    needToShow(x) {
        let locale = this.$i18n.locale;
        return x[locale] !== undefined;
    }
    usePicture(x) {
        if (x === undefined) return false;
        let locale = this.$i18n.locale;
        return x.usePicture !== undefined && x.usePicture[locale] !== undefined;
    }
    getPicture(x) {
        let locale = this.$i18n.locale;
        return `pictures/${locale}/${x.usePicture[locale]}`;
    }
}
export default HomePage;
</script>