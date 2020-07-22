<template>
    <div class="container-fluid" >
        <div>
            <div class="cate-header">{{ $t("action.control")}}</div>
            <div class="cate-body">
                <button class="btn btn-info" @click="random">{{ $t("action.randomplay") }}</button>
                <button class="btn btn-info" @click="stopPlay">{{$t("action.stopvoice") }}</button>
                <button class="btn btn-info" :class="{ 'disabled': autoCheck }" @click="overlap" :title="$t('info.overlapTips')">
                    <input class="checkbox" type="checkbox" v-model="overlapCheck">
                    <span>{{ $t("action.overlap") }}</span>
                </button>
                <button class="btn btn-info" :class="{ 'disabled': overlapCheck }" @click="autoPlay">
                    <input class="checkbox" type="checkbox" v-model="autoCheck">
                    <span>{{ $t("action.autoplay") }}</span>
                </button>
            </div>
            <div class="cate-body">
                <span>{{ voice.name ? $t("action.playing") + $t("voice." + voice.name ) : $t("action.noplay") }}</span>
            </div>
            <audio id="player" @ended="voiceEnd(false)"></audio>
        </div>
        <div v-for="category in voices" v-bind:key="category.categoryName">
            <div v-if="needToShow(category.categoryDescription)" class="cate-header">{{ $t("voicecategory." + category.categoryName) }}</div>
            <div class="cate-body">
                <button v-if="needToShow(voiceItem.description) && !usePicture(voiceItem)" class="btn btn-new" v-for="voiceItem in category.voiceList" v-bind:key="voiceItem.name" @click="play(voiceItem, category.categoryName)">
                    {{ $t("voice." + voiceItem.name )}}
                </button>
                <img v-if="needToShow(voiceItem.description) && usePicture(voiceItem)" v-for="voiceItem in category.voiceList" v-bind:key="voiceItem.name" v-bind:src="getPicture(voiceItem)" @click="play(voiceItem)"/>
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
    max-width: 100%;
    word-wrap: break-word !important;
    word-break: break-all !important;
    white-space: normal !important;
}
.checkbox {
    display: inline-block;
    vertical-align: middle;
    margin: 0 1px 0 0;
}
img:hover{
    transform: scale(1.1);
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
    voices = VoiceList.voices;
    autoCheck = false;
    overlapCheck = false;
    voice = {};
    playingAudio = new Map()

    play(item, category){
        if (this.overlapCheck) {
            let audio = new Audio("voices/" + category + "/" + item.path);
            this.voice = item;
            let key = item.path;
            while (this.playingAudio.has(key)) {
                key = key + "$";
            }
            this.playingAudio.set(key, audio);
            audio.onended = () => {
                this.playingAudio.delete(key);
            };
            audio.play();
        } else {
            this.stopPlay();
            let player = document.getElementById('player');
            player.src = "voices/" + category + "/" + item.path;
            this.voice = item;
            player.play();
        }
    }
    stopPlay(){
        let player = document.getElementById('player');
        player.pause();
        this.playingAudio.forEach(datum => {
            datum.pause();
        });
        this.playingAudio.clear();
        this.voiceEnd(true);
    }
    voiceEnd(flag) {
        if(flag !== true && this.autoCheck) {
            this.random();
        } else {
            this.voice = {};
        }
    }
    random() {
        let tempList = this.voices[this._randomNum(0, this.voices.length - 1)];
        this.play(tempList.voiceList[this._randomNum(0, tempList.voiceList.length - 1)], tempList.categoryName);
    }
    autoPlay(){
        if (this.overlapCheck) {
            return;
        }
        this.autoCheck = !this.autoCheck;
    }
    overlap() {
        if (this.autoCheck) {
            return;
        }
        this.overlapCheck = !this.overlapCheck;
    }
    _randomNum(minNum, maxNum) {
        switch(arguments.length) {
            case 1:
                return parseInt(Math.random() * minNum + 1, 10);
            case 2:
                return parseInt(Math.random() * (maxNum - minNum + 1) + minNum, 10);
            default:
                return 0;
        }
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
