import re
from typing import Iterable

import requests
from pywikibot import Page
from pywikibot.exceptions import InvalidTitleError
from pywikibot.pagegenerators import GeneratorFactory
from pywikibot.tools import itergroup

from utils.config import get_data_path
from utils.sites import cm, mgp
from utils.utils import get_commons_links, get_page_list, get_continue_page, save_continue_page

exclude = {'Logo youtube.png', 'Bilibili Logo Blue.svg', 'Bilibilitv-logo.png', 'Nijisanji_temp.png',
           'Twitter logo.svg', 'Nijisanji Logo.png', 'HololiveMusicLogo.png', 'TikTok Logo.svg',
           'Holodex Logo.svg', 'hololive.PNG', 'YouTube Logo icon.png', 'Twitch Logo.png',
           'Hololive production.png', 'Flag_of_China.svg', 'Flag_of_Japan.svg', '萌薇头像.png',
           'AcFun Logo.svg', 'AVI联盟标志.png', '虚研学园logo（透明底）.png', '虚研社去底logo.png', 'NIJISANJI.png',
           'ChaosLive图标.png', 'Commons-emblem-success.svg', 'Emo わいのわいの.png', 'Emoji u1f3f3.svg', '粉丝勋章 舰长.png',
           'Nav-nijisanji-v20fix.png', 'Disambig gray.svg', '大萌字.svg', 'TwitCasting Icon.svg',
           'Zh conversion icon m.svg', '大萌字.svg', 'Hololivetoulogo.png', 'Nanaon-logo.svg',
           'Ambox currentevent.svg', 'NationalismMoegirl.png', 'Information icon.svg', 'TwitterVerifiedIcon.png',
           'Folder Hexagonal Icon.svg', 'Shengliwenhua logo.jpg'
           # from commons vtuber template images
                                        '早雾聖奈 头.png', '古堡龙姬（展示图）.jpg', 'Akuno Rock.jpg', '星野悦w（半身立绘-白底）.png',
           '黄蜂 介绍图.png',
           '犽月Kitsuki（头部立绘-表情差分-透明）.png', '瑟薇尔（半身立绘-表情差分）.png', '林檬洲Hayashi（全身立绘-1080p）.png',
           '可可洛.jpg', 'Kaga sumire.png', '凛星 脸.jpg', '爱尾千影.jpg', '东鸟头.png',
           'ReVdol2 logo (small yet less blank).png', '弥塞里娅-icon1.jpg', 'WAKTAVERSE풍신.png',
           '庞小莹小图.jpg', 'Iroha1.jpg', '钢板Reacis（展示图）.jpg', 'Holostars 3.png', '波塔兔 介绍图.jpg',
           'Miriya头.jpg', '一串葡萄丸子-icon1.jpg', 'VWP Kaf W2x MkI.png', 'WAKTAVERSE비밀소녀.png',
           '艾因头像2 0.png', '风云社Logo.jpeg', 'VCPLogo.png', '墨菲斯特（展示页）.jpg', '撒达 介绍图.jpg',
           '第七圣地.jpg', '呜哇固.jpg', 'Hololive SpadeEcho 2.png', '千时静半身.jpg', 'OROGIRES.png',
           '夏盐半身.png', '猫邮社：猫小鹰.png', 'AizawaEma - Portrait.png', 'Talent li ji thumbnail.jpg',
           '猫邮社：思廿.png', 'WAK logo.svg', '初颜.jpg', 'ENA正头.jpg', '猫邮社：摩亞.png', '七瀬せな.jpg',
           'VCP全员.png', 'Deat.jpeg', '恋水时 头.png', 'Witch Dali Sweet.jpg', '樱吹雪.png',
           '维斯卡-封面.png', '结成梓 头.jpg', '千橙全身立绘.jpg', 'MOFU-F logo.jpg', 'Huaibao.png',
           'Yymm-icon2.jpg', '麻宝（番茄形象-QQ）.jpg', '子茶（Live2D展示）.png', 'XUEpro.png',
           '礼墨（专栏展示立绘）.png', 'Takeshi-icon-2.png', '北立交桥（logo-白底）.jpg', '埃利塔Elitta（曲绘）.png',
           'Yukamomo.png', 'Mana头.jpg', '时堇 Tokki（变身前）.png', '爱尾家背景图.png', 'Yomenomoemi.png',
           '哪nana cubism.png', '宫本夏凌1.png', 'Mari-icon1.jpg', 'Lepuslive（logo-白边）.png',
           'Kurokawa-3.png', 'Virtuareal link Isabella.png', '哈鲁卡 logo.webp',
           'Chobits live logo 镂空.png', '萧箬薇半身.jpg', 'Isekaijoucho head.jpg', '恋恋-icon1.jpg',
           '一串葡萄丸子-icon2.jpg', 'Srk-icon2.jpg', '路普lupu（全身立绘-白底）.jpg', '陆婉莹.jpg', 'Saki头.jpg',
           '阿尔瓦（全身立绘）.png', 'PikaMain001.JPG', 'Teresa Head.png', '慕影真（展示页）.jpg',
           'HoshinoMiya.jpg', '路伊丝-icon1.jpg', '小桃（2.0模型-头部立绘-表情差分）.png', '猫邮社：有理.png',
           '满月-icon2.jpg', '弥塞里娅-icon2.jpg', '妙妙（立绘-到胸口）.png', 'WINKS Logo.png',
           '普罗维登企划长logo.png', 'Hololive 4.png', 'Project Lupinus.png', 'Ine像.png',
           'AnotheR Color（logo-紫色白边）.png', '灰猫nns.jpg', 'Logo白横.png', '南音乃像.jpg',
           'B.A.S.E一期生.jpg', 'Aki 0th Portrait.jpg', 'Ruriko头.png', '绯夜（海葵形态）.png',
           '海德薇Hedvika（展示图-初始形象）.jpg', '七海.jpg', '猫邮社：杜松子（2.0睡衣）.png', 'Yoyo头.png',
           'Sukotte Illustration.png', '双葉すい.jpg', 'Huiyinhaine-icon1.jpg',
           '贝伦 Baylen（全身立绘-1080p）.png', 'Himesaki1.jpg', '废魂儿（头部）.png', 'Norio6.png',
           '宫园凛 头图.png', 'VID logo(New).png', '梅芙洛 head2.png', 'Lucia-icon2.jpg',
           '怜奈-icon1.jpg', 'ADR.png', '橘九立绘.png', '舒三妈 头图.png', '新科动漫台标（中央新影-白底）.png',
           '柚一全身立绘.PNG', 'Harusaruhi head.jpg', 'Virtua real.png', 'Aogiri rogo master.svg',
           'WAKTAVERSE왁파고.png', '神川奈-icon1.jpg', 'EILtwitter.jpg', '小偶像-icon1.jpg',
           '沙梨叶 Suriel（展示图-初始立绘）.jpg', '尤米-icon1.jpg', '七叶琉伊立绘.jpg', 'Rua头.png',
           '茉吱202178.jpeg', 'Riotmusic logo.png', 'Kouwu.png', '链式猫网络.png', '时音.jpg',
           '无限殿-0409-3.jpg', 'BENO.jpg', '提丰头test.jpg', '晨星祭.jpg', 'Diva logo.png',
           '虚研社：紫海由爱（2.0）.png', '陆桃全身立绘.png', 'ANMRlogo2XS.png', '纱鱼.png', '源求 介绍图.png',
           'Serena头白底.jpg', 'Moonlight-icon.png', 'Chiram-icon1.jpg', '喵喵头.jpg',
           'Fukugakuencho Illustration.png', 'WAKTAVERSE융터르.png', 'EileneChannel.jpg',
           'Marble-creators-top-logo.svg', 'Mz社徽.png', '鹿岛山月 吃我喵喵拳（全身立绘）.png', 'Hololivejp5th2.png',
           'Tsukito Hana.jpg', '白小葭.jpg', 'Haya-icon1.jpg', 'AIENICONALP.png', '悠娜 介绍图(1).jpg',
           'Venus（logo）.jpg', 'Veemusic logo neon.png', '继 Tsugi（全身立绘）.png', 'Oto头.jpg',
           'Yuki Murasakii.jpg', 'Ironmouse Icon.jpg', '幻想社logo（蓝底白字）.png', '雪璃 介绍图.jpg',
           'Hololive 0.png', '爱尾星七.jpg', '珈乐Carol 公式.jpg', 'Nyatasha Nyanners Icon.jpg',
           'VIichan像.png', '花音.jpg', 'Serena头.png', '八海.jpg', 'Kirara1.jpg',
           '樱乃诱魅 介绍图.png', 'HP member lulu.png', 'Future Land（logo）.png', '蜜恩头1.png',
           'Miya-icon2.jpg', 'Lilith1.jpg', 'Redcircle logo.png', 'NekotaTsuna.png',
           'TokimoriSeisaSmall.png', 'Ichinose uruha.png', '茯苓TC.png', '镜喵 介绍图.jpg',
           '根本不二子（半身-白底-1080p）.png', '惺忪喵.jpg', '露珀塔立绘.png', 'Lzsn图标.png',
           'The Moon Studio Logo.png', 'RjOJ8Rj- 400x400.jpg', '伏见香音 模板用图.jpg', '不举栗萌（专栏展示立绘）.png',
           '云光计划 logo.jpg', 'CloudConnecting.jpg', 'NoWorld（新logo-透明）.png', '璃鱼 介绍图.png',
           'A-SOUL透明.png', '白卷玲奈头.jpg', 'ColorLink.png', 'Hololive 1.png',
           'VWP Isekai W2x MkI.png', '超电小电视.png', 'Fugami Nanana Illustration.png', '山梨.png',
           'Nyarin.jpg', '库姬头.png', '千铃SR head sculpture.jpg', 'Beni-icon2.jpg', 'Ritsu头.jpg',
           '病院坂（专栏展示立绘）.png', '满月-icon1.jpg', '有栖川曜 head.jpg', 'Dissko.jpg', '凰清音 模板用图.jpg',
           '芙拉Fula（全身立绘-1080p）.png', '姜九竹 模板用图(2).jpg', 'Mea头.jpg', 'Talent shatang image.jpg',
           '恋恋-icon2.jpg', '猫邮社：灯夜-2022.png', 'Haruya 0th Portrait.jpg', 'Mimitus.jpg',
           'RuoZhi1.png', '托丽 head.jpg', '伊芙Eve（展示图-初始形象）.png', 'SOW社团logo（抠图）.png', '夜岚头.png',
           '音仙吕.jpg', 'Lilika-icon-2.png', '喀秋莎·秋明1.jpg', '虚研社：幽灵子辰.jpg',
           '蛇喰泠（全身立绘-白底带文字）.jpg', 'Hololive other3.png', '幽夜 head.jpg', '悕夏 介绍图.jpg',
           '东爱璃01.jpg', '新科娘一周年航天主题.webp', '饭团半身照.jpg', '一颗芽 介绍用.jpg', '日奈希久-icon2.jpg',
           '诺拉·海蒂斯.jpg', 'Kogure Piyoko.jpg', '古守血遊.jpg', '龙裁司TC.png', '夏絵Erza（展示图-初始形象）.png',
           '一颗有栖 介绍用.jpg', '小鸟头.png', 'Noworld b站头图.png', 'Akari头.png', '唐乐乐-icon2.jpg',
           '李豆沙（专栏展示立绘）.png', 'VSPO-logo.png', 'HP member riiko.png',
           'Hoshihime Kirara Illustration.png', '猫大头.jpg', 'Keroro-icon2.jpg', '栗娜 logo.webp',
           'Hime Hajime Icon.jpg', 'Enomiya1.png', 'Momo1.jpg', '经纪人—黑0.png', '萝半鸽 模板用图.png',
           '罗菈Rola立绘.png', '一般路过阿宅.png', '约修亚（展示页）.jpg', '艾芮 头像2.png', '沃瑞尔 q版.jpg',
           'Miya-icon1.jpg', '茶茶-icon1.jpg', 'Kuma-icon1.jpg', '双月Yuna.jpg', 'Paryi头白底.jpg',
           '鈴葉千早（展示图-初始形象）.png', '猫邮社：尤狸.png', 'Mitsuki头.png',
           'Etra twitter profile images 400x400.jpg', 'いろどり芸能郵便社.png', '虚研社：小柔（修女）.png',
           'Hololive other.png', 'Anon头白底.jpg', '嘉然Diana 公式.jpg', 'QD头.png', 'Koria头test.jpg',
           '九条Mashiro头.jpg', '芭娜娜全身立绘.jpg', 'Ciela.jpg', '虚研社：夜铃（低清）.png', '千鸟Icon.jpg',
           '蕾蒂希雅-头.jpg', '六条阳羽 介绍图2.png', 'Sakumaniina-icon2.jpg', '伊兹 Iz（全身立绘）.png',
           '灯瑠-icon2.jpg', 'Huiyinhaine-icon2.jpg', 'Hololive cn2.png', '蔻蔻（同人图）.png',
           'Hanser P.jpg', '栗子酱 Thumb.jpg', '猫邮社：Sandy.png', '诺诺12.jpg',
           '山椒阿露波（半身立绘到胸口-透明）.png', '雪貂女学院logo.png', 'Renana.jpg', '澈丽妹妹 logo.jpg', '糖啾头.png',
           'Muse1.jpg', 'Jingburger像.png', 'NoiR新live2d立绘透明.png', 'Akino.png', '白神遥Haruka.jpg',
           '兔瑞卡 介绍图.png', 'Hibiki Yui Illustration.png', 'EOE女团（logo-透明,4：3）.png', 'KKKHK1.jpeg',
           '夜宵Eve像.png', '宋三岁（全身立绘-白底）.jpg', '输回巡 模板用图.jpg', '云玉鸾1.jpg', 'Lovechan thumb.png',
           '诺米尔（海葵形态-透明）.png', '纱伊-icon1.jpg', 'Amalis.jpg', 'Sougetsueri.jpg', 'Haru头.jpg',
           '茜-icon2.jpg', '月乃盈（专栏展示立绘）.png', '毛多多-icon2.jpg', '修莉雅半身.jpg', '沐莺.jpg',
           'RIME Phenomenon.png', 'Upd8 Vector.svg', 'Gosegu像.png', 'Virtuareal 16.png',
           'Zeroprologo.png', '椰栗Yeri（全身立绘）.png', '小柒nana-icon1.jpg', 'Reikira头.jpg',
           'Suou Patra.jpg', '晴奈子.jpg', '阿塔斯 Altas（全身立绘-1080p）.png', 'Takna Portrait.jpg',
           '玖麻头2.png', '774pien.jpg', '阿露丝头.jpg', '星研社（logo）.jpg', '极昼Polar-D（logo-白底）.png',
           '瓦瓦子-0.png', '空风Kuu（直播画面）.png', '醒爷头.png', 'Mochimochi Sakura Illustration.png',
           'MochiPro member 20200222.png', 'Toi Haruka Predebut.jpg', 'KAFU Icon 400x400 1.jpg',
           '花寄-花丸晴琉.jpg', '木南工坊.png', 'HP member yamai.png', '双荔立绘.jpg', '千露 介绍图.jpg',
           '皆月游兔 介绍图.jpg', '雪鹤 logo.webp', 'Reno头.png', 'Kaminari Qpi.png', '阿卡林.webp.jpg',
           'Chelseas.png', 'Inuchiyo Kokona Illustration.png', 'Kson Icon.png', 'Hina Misora.jpg',
           '霏欧娜Fiona（全身立绘-初始形象-白底）.jpg', '完美世界（logo）.png', 'MicoSekishiro 500x500.png',
           '猫邮社：幸森诗音(头像).png', '惠惠megumi-icon2.jpg', '绫奈奈奈 校服 外套ver..jpg', '团小哈（展示页）.jpg',
           'Cytolive@4x.png', '亚哈 脸.jpg', '金克茜 头图.png', 'Mitsurugi Lia - Profile Picture.jpg',
           'Silvervale Icon.jpg', '纱伊-icon2.jpg', 'Mei头.jpg', '纸片人Novus（logo-横式-官方）.png',
           '774inc.svg', '茶茶-icon2.jpg', 'HP member nenene.png', '星宫颜-icon1.jpg',
           'SugarLuriclogoXS.png', 'Croven教团logo（抠图）.png', '小偶像-icon2.jpg', '于川流丹.jpg',
           '伊欧-icon2.jpg', 'Mojuko-icon1.jpg', 'Eilene.jpg', '猫屋敷错 介绍图.jpg', 'RikaV.jpg',
           'Hanabusa Lisa.png', '西木木木栗头.png', '灯瑠-icon1.jpg', '馅蜜椿 模板用图.png', '猫邮社logo.png',
           'The Virkyrie（logo-透明,4：3）.png', 'Llcntlys.png', 'Beppy2.jpg', 'Mochipro Icon.png',
           'Lionheart1.jpg', 'VEgo Logo.png', 'Kurumi noa.png', 'Virtuareal 15.png',
           'Warabe1.jpg', 'Lucia-icon1.jpg', '猫脑过载.png', 'Rurineluna.png',
           'Kizunaai thumb.png', 'Beni-icon1.jpg', 'EIL2.webp', '日奈希久-icon1.jpg',
           'Zentreya Icon.jpg', 'Virtuareal 6.png', 'Yakumo beni.png', 'Arisa头.png',
           'NoiR新头图.jpg', '風和凛 Fuwari.png', '虚研社新logo.svg', '桥和一奈b站.jpeg', '极光社logo.png',
           'Balus member 20201009.png', 'EIL4.webp', '妖澜澜 模板用图.png', 'Jururu像.png',
           '林原白夜 头.jpg', 'Shiori头白底.jpg', 'Yuki-icon2.jpg', 'React logo.png',
           'EroS（logo4-白边）.png', '千鹤Chizuru（全身立绘-1080p）.png', '米修恩Michonne（展示图-初始形象）.png',
           '猫屋敷尼娅（展示图-初始形象）.png', 'Virtuareal-star.png', '椰芙eve.webp', 'HNSTlogo.png',
           '人形冬萌立绘.png', 'Lecia-icon1.jpg', 'Commons-emblem-issue.svg', 'DotLIVE.jpg',
           'Saga Shinobu.jpg', '文静.jpg', '虚研社：黎歌（低清）.png', '露露娜 头图.png', '凯洛斯 head.jpg',
           '虚研社：冰糖（初始立绘）.png', 'Virtuareal 11.png', '亞崎凩Akira（全身立绘-1080p）.png', '秋凛子.jpg',
           'Hololive Yogiri.png', '猫邮社：苳灵.png', '飞鸟夜 头.jpg', 'Palleteproject logo.png',
           '棋盘-头.jpg', 'Haruka头.jpg', '花寄-野野宫Nonono.jpg', 'Hoshina Suzu.jpg', '玛安娜-icon1.jpg',
           'HNSTlogoXS.png', 'Hololive 2.png', '12138.png', 'Sakumaniina-icon1.jpg',
           '蜜雨（Live2D展示）.png', 'Ae-icon1.jpg', 'WACTOR logo white.png', '虚研社：艾露露.png',
           'Chofie斐雅（全身立绘-白底）.jpg', '芙泥 logo.webp', 'HiyocrologoXS.png', 'Miu头.jpg',
           '头子 阿b.jpg', '森羽头像.jpg', 'MarySaionji 500x500.png', 'Mugenlive logo.png',
           '砂糖 云光计划.jpg', 'Aipii thumb.png', 'Svhs.png', 'Inumaki Himari.jpg',
           'VWP Rlm W2x MkI.png', 'Lecia-icon2.jpg', '红莲oGuren（全身立绘-白底）.jpg',
           'Eraverses Sprites.png', 'IRIAM Logo White.png', '路普lupu（logo）.jpg',
           '奈姬niki（萤火虫虚拟舞台）.png', 'Kamino Hikari Illustration.png', 'Revdol logo.png',
           'Nanoha头.jpg', 'Zero-icon.png', 'Rabutyan1.jpg', '小千村柚柚 2月新衣 立绘 压缩.webp',
           'Natsumi Moe.jpg', 'Keroro-icon1.jpg', 'Ito Shinonome.jpg', '华枝雀Harpy（展示图）.jpg',
           '芥茉-icon2.jpg', 'Qkls.png', '伊芙头.png', '小春Koharu（展示图-初始形象）.png',
           'Epoch Link（社团logo-透明）.png', '海月薰（专栏展示立绘）.png', '铃果全身立绘.jpg', '彩虹酱哇（全身立绘-白底）.png',
           'Virtuareal 17.png', 'Virtuareal 5.png', 'Olivia-icon.png', 'CHIPS50% logo.png',
           '阳炎头像1.jpg', '艾白.jpg', 'Kuma-icon2.jpg', '爱夏.jpg', 'Kaga nazuna.png',
           '朝日奈乃（头部立绘）.png', '结缘屋logo（抠图）.png', '莎小咩.jpg', 'WAKTAVERSE해루석.png',
           'YOMEMI PROFILE.jpg', '捷伊德Ja1de（展示图）.jpg', '猫邮社：泛晓.png', 'Emina-Studio.webp',
           'Kamitsubaki studio.svg', 'Veibae Icon.png', 'EliSougetsu 500x500(4).png',
           '蕾琳Leylin（展示图-初始形象）.png', '维克特瑞-icon2.jpg', 'Overidea white.png', 'Holostars 2.png',
           '虚研社：卡诺娅.png', '虚研社特别合作：青井葵.png', 'Norns Project.png', '中国绊爱像.jpg',
           'VirtuaReal fourteen.png', '椰乃（全身立绘-白底阴影）.png', 'VAPAlogo2XS.png', 'WAKTAVERSE김치만두.png',
           '伽兰Kana head sculpture.png', '八乙女noe1.jpeg', '空格子bot 介绍图.png', '尤特小图.jpg',
           '花寄女子寮标志.png', 'Unlimited Logo 2.svg', 'Xsybx.png', '纸片人计划（logo）.png',
           'ZHIZHIxs.png', 'Virtuareal 2.png', '花香咲（展示图）.png', 'Paryi头.png', 'Inga头 新.jpg',
           '希希新头1.jpg', '爱尾美玲.jpg', 'ShinomiyaRuna - Portrait.png', '沙织-0409-1.jpg',
           'BraveGroupLogo.svg', '月夜见九十九 模板用图.jpg', '蕾蒂头4.png', '星禾（Live2D展示）.png', '西魔幽像.png',
           '眠夜Yoru（展示图-初始形象）.png', 'Virtuareal 4.png', '花崎Haki（展示图-初始形象）.png', '芥茉-icon1.jpg',
           '糯依头像.png', '步玎立绘.png', '度日头.png', '瞳凛二代目立绘上半身.png', 'Virtuareal 8.png',
           'Rio-icon.png', '异世界女团logo.png', '费不燎（设定图）.jpg', '佐仓双夜头.png',
           'VWP Koko W2x MkI.png', '夕映结社logo.png', '修格头.png', '茜菲.png', '小可 头图.png',
           '光年神话logo（抠图）.png', '霧間風-icon2.jpg', 'Talent axiu thumbnail.jpg',
           'NOVA-Project S（logo-透明）.png', 'VPlogo.png', 'ACGlive（字母logo-抠图）.png',
           'Virtuareal Star Hanser 1.png', 'Yymm-icon1.jpg', 'Hoshimeguri Gakuen.webp', '艾瑞思.jpg',
           'Vshojo logo.png', 'Kumagaya1.png', 'Sumeragi Pal.jpg', '浦兰 title.jpg',
           '柑橘社logo.png', '陆仙姑 介绍图.png', 'Palow-icon.jpg', 'Zmzxs.png', '虚研社：Noir.png',
           'Blanche Fleur.jpg', '小班长kusa（展示图）.jpg', '艾米 logo.png', 'Nia1.jpg', 'ADRC.png',
           'Chiaki头.jpg', '苏离 模板用图(1).jpg', '喵年半身.png', '星宫颜-icon2.jpg',
           '夏野 Natsuno（全身立绘-2.0形象）.png', '卡嘉明kagamin（全身立绘）.png', '戌夜初Hajime（全身立绘-1080p）.png',
           '盲盲立绘.png', 'HololiveID123.png', '猫箱nekobako（logo-修复）.png', '红晓音 mage.png',
           'Confusion grey.svg', 'HP member kanna.png', 'Awa-self.png', 'MInori头.jpg',
           '卡连Kallen（全身立绘-1080p）.png', '茜-icon1.jpg', '蕾伊娜Reyna（展示图-初始形象）.png',
           'Vomnis（logo-白底）.jpg', '猫白ShiroNeko（展示图-初始形象）.png', '玺月兔兔（Live2D展示）.jpg',
           'VWP Haru W2x MkI.png', 'Riya-icon1.jpg', '芄Makino head.jpg', 'WAKTAVERSE미츠네하쿠.png',
           'CharlotteShimamura 500x500（02）.png', 'ShadowLogohOuOu.png', '竟夕（展示图-初始形象）.png',
           '柚子花1.jpg', '胡桃-icon2.jpg', 'S.S.R logo.jpg', '张亮（猫形象logo-666p）.png',
           'Amano Oto.jpg', '白鸟萌月头.png', '伊南娜-body-01.jpg', '蒂悠·普拉缇头图.png', 'Kogara toto.png',
           'Erio头.jpg', 'ChobitsLive MoNi头.png', '猫邮社：白黑卡扣.png', '曙光收容logo.jpg', '月见.jpg',
           'EIL1.webp', '4d80e1029698d61c9f7c003240be57fb8405c6a5.jpg', '佐娜半身.png', '千耘-icon1.png',
           'Mireille Kuuma.jpg', 'VirtualConcept（logo-透明）.png', 'Mizuki-icon.png',
           'Hioki Yachi Illustration.png', 'Cache -4a0637897bd270..jpg', '雪花Yuke 模板用图.png',
           '虚研社特别合作：赤五教教主小亮.png', '娜纱Nasa.png', '戴安娜半身.png', 'Ui-icon.png', '弥海星砂 头 改.png',
           'Higasa头.jpg', 'Yukichi-icon.png', 'Ae-icon2.jpg', '风霁月.jpg', '小卯-コウサギ.jpg',
           'Haya-icon2.jpg', '霧間風-icon1.jpg', 'Fanjie 0th Portrait.jpg',
           'Talent naizi thumbnail.jpg', 'Kuramochi Kyoko Illustration.png', '留歌.jpeg', '超V学园.png',
           'Virtuareal link suxing.png', 'Projekt Melody Icon.jpg', 'Hololivejp6th.png',
           '迪蒙格拉斯（展示页）.jpg', '千耘-icon2.png', 'Koko-icon.jpg', 'Rin头.png', '怜奈-icon2.jpg',
           '扶桑头.png', '花寄-小东人鱼.jpg', 'EIL5.webp', '神川奈-icon2.jpg', '桃垣依（全身立绘-白底）.png',
           'Vidol logo.png', 'Nazuna Icon.png', '鹤森 头图.png', 'VirloProject（logo-红色系白底1：1）.png',
           'Sakura-icon.png', 'Emiya头.png', 'EIL6.webp', 'Holostars 1.png', '七柠新立绘.jpg',
           'Oguri Mel Illustration.png', '夜久Yahisa（全身立绘-1080p）.png', 'Asumi Sena.png', '一只卡莱尔头.png',
           '叶月Hatsuki（全身立绘-1080p）.png', '雨声奏 Kanade（全身立绘）.png', '猫邮社：可伊.png', '菲列米塞瓦托提斯TC.png',
           'Vivid.png', '猫貉神狸 介绍图.png', '思绪头图.jpg', '立花结那 新小图.jpg', 'Mizuno Levi.jpg',
           '伊尔伊Iroi（展示图）.jpg', 'Shino Laila.jpg', '伊吹千代 头.png', 'Entum Logo Horizontal.png',
           'Shiori头.png', 'Claude-icon.png', 'Kizuna AI Kabushikigaisha Logo Fit White.png',
           'HIMEHINA Logo Text.svg', 'Noripro T.png', '克罗刻 head.jpg', '東雲凪 头.png',
           '伊欧-icon1.jpg', '雨宮依亜 头.jpg', 'Mizuyo Portrait.jpg', '矢泽大凤半身.png', '猫邮社：纳米.png',
           'NoiR可爱立绘.png', '司判 head.jpg', '乐颜-安菟.PNG', '夏行美.jpg', 'Chloe-icon.png',
           '哎咿多logo.png', 'Hana头.jpg', '白辞 head.png', '白灯不拖更 头像.jpeg', '机萪七夕立绘.jpg',
           'Hololive 3.png', 'Chips project logo.png', 'Project Vnicorn.png', '长月春雪（展示页）.jpg',
           '胡桃-icon1.jpg', 'HololiveENCouncil.png', '花满2代正面头.png', 'Tosaki Mimi.png',
           'Hizuki Miu.jpg', 'HololiveSTAFF.png', '莲汰.webp', '夏鹤仪1.png', '神奈希 模板用图.png',
           '猫姬琥珀 Vtuber.png', '狐狐.jpg', '田中姬铃木雏挂件.png', 'Balus.png', 'Ein头.png',
           '虚研社特别合作：格蕾缇娅.png', 'HololiveEN1.png', '瑞贝莉亚.jpg', 'Bazooka 介绍用图.jpg',
           'Satousatou-icon1.jpg', '永恒娘（图绘）.jpg', 'Mojuko-icon2.jpg', 'Aien5.png',
           'Transparent Akkarin.jpg', '夕兔头图.png', '猫邮社：啾铃.png', 'Meruto头.jpg', '雨街 脸.jpg',
           'Virtuareal 1.png', '笙妤 头图.png', 'Rime1.jpg', '诺祁Nocchi（展示图-初始立绘）.png',
           'END临时logo.jpg', 'Yue Saohime.jpg', 'Neco.png', '早乙女雪葵（半身立绘-表情差分）.png',
           'Kisaragi ren.png', '哈娜酱.png', 'Shin1.jpg', '战斗吧歌姬logo tr.png', '悠米Yuumi.jpg',
           '希洛TC.png', '白底菫妃奈.jpg', '小亚.jpg', 'CharlotteShimamura 500x500.png',
           '月隐空夜-icon1.jpg', 'Hololive Civia.png', '结城蓝-Larimar.jpg', 'P-SP.png',
           'SEKAI youtube profile.png', '爱尾家 Logo.png', '钟持.jpg', '双月Lia.jpg',
           'Holostars4th.png', 'Virtuareal-star-ureme.png', '路菲尔（设定图）.jpg',
           '绫濑川Ayase（展示图-初始形象）.png', 'ロゴ 透過.webp', '律花 Ritsuka（全身立绘）.png', 'MaeSond（logo-白底）.jpg',
           '嫣然laurelB站.png', '库玛斯特KuMaster（展示图）.jpg', 'Virtuareal 3.png',
           'Nameless Project Logo.jpg', 'Dodo（生日会宣传图）.jpg', '波莉Pori（展示图-初始形象）.png',
           'Virtuareal link Karon.jpg', '异世界女团.jpg', '神代卡露（展示图-初始形象）.png', '贝拉Bella 公式.jpg',
           '佐久零音 介绍图2.png', 'DovelifeProject logo.jpg', '新科娘Vup.jpg', '白桃hakutou头.png',
           '林莉奈 正面絵 x.25.png', 'Coco 千鸟Official.jpg', 'Ninico头.jpg', '玛安娜-icon2.jpg',
           'Ferret三世.png', 'Miraiakari.jpg', 'Lilpa像.jpg', '维克特瑞-icon1.jpg',
           'Madoka-icon2.jpg', '夜萤秋月 head.jpg', '新夏装全身立绘.jpg', 'PLIVYOU1.png', '唐乐乐-icon1.jpg',
           'Nowhere vtuber.jpg', 'Naki-icon.png', '狄灵计划logo.jpg', 'Nanaseunia-icon1.jpg',
           '𬬭特.png', '莉莉安原绘.png', 'Template-info.svg', '如月koyori像2.jpg', 'Kurari Rose.jpg',
           '毛多多-icon1.jpg', 'Wodka.png', 'Kanon头.jpg', '蓝白2.0.png', 'NoiR的透明立绘.png',
           'Riya-icon2.jpg', 'Apricot (Froot) Icon.jpg', '江惠惠半身.png', '星雾初始立绘1.jpg', '星汐1.png',
           'Vgaming logoyoko.png', '季毅.jpg', 'Virtuareal 7.png', 'Virtuareal link.png',
           'Mikado Illustration.png', '阿惬.jpg', '尤米-icon2.jpg', '咬应明 模板用图.jpg',
           'Iori Nemea Illustration.png', 'Yuki-icon1.jpg', 'ProproProduction.webp', '安菟 logo.png',
           '小希（3.0模型-头部立绘-表情差分）.png', '云子KumokoB站.jpeg', '笙歌-4号机宫廷款自拍.png', 'Chiram-icon2.jpg',
           'Virtuareal 12(2).png', 'Virtuareal 9.png', '幽鹭头.png', '夜矢绫芽半身.png', '次元镜像.jpg',
           'Vmezon.png', '海紫米头图.png', '星娅-head.jpg', '熵增EI Logo3.png', '超次元学院logo.png',
           '魔女公司.png', 'Ruby-icon-2.png', '纸片人Novus（logo-竖式）.png', 'Mari-icon2.jpg',
           'Madoka-icon1.jpg', 'NoWorld概念图.jpeg', '向晚Ava 公式.jpg', 'Okome 20210528.jpg',
           '小柒nana-icon2.jpg', 'Mimi Yukinoshita.jpg', 'Nebula-Beat Logo.png', '营业十三部.jpg',
           'Michelle-icon.png', 'Holostars Logo.png', '悠梦する！女仆咖啡厅！（logo-透明）.png',
           '仙梓哟（全身立绘-白底）.png', 'Virtuareal 10.png', '不吃饭の书生--插图2.jpeg', '彗星号 LOGO.png',
           'MicoSekishiro 400x400.png', '惠惠megumi-icon1.jpg', 'Talent joi thumbnail.jpg',
           '花寄-鹿乃.jpg', 'Naru-icon.png', '艾斯忒Esther（展示图-初始形象）.png', 'TempusHolostars.png',
           '天瀬椿 头.png', '成海晴爱.png', 'Mq pZOp9 400x400.jpg', 'SiriusProject LOGO01.jpg',
           'Akai Satan.jpg', 'Virtuareal link Nox.png', '雪域Provealms（logo-灰底）.jpg', '赫卡Tia立绘.jpg',
           'Tachibana hinano.png', '绮露Hades（展示图-初始形象）.png', 'Lucca.png', '极夜Polar-N（logo）.jpg',
           'Hololive luna.png', '新月岚Normal.png', 'Overidea banner 2019.png', '鸠羽lin（半身立绘-透明）.png',
           'Enfer头.jpg', 'AstralisUP头.png', '月翎-head.jpg', 'Yy5.png', 'Nanaseunia-icon2.jpg',
           '可可拉 头像.png', '咩也爷头.jpg', '乃琳Eileen 公式.jpg', '粢华与绛弦（全身立绘-白底）.jpg',
           '伊橙（全身立绘-白底）.jpg', 'Daibi 头.png', '阿媂娅像.jpg', 'PatraSuou 500x500.png',
           '路伊丝-icon2.jpg', '月隐空夜-icon3.jpg', '琳 千鸟Official.jpg', 'DDDD.png', '雪乃衣（全身立绘）.png',
           '林岳风（展示页）.jpg', '白黑黑白旧头图.png', 'SouyaIchikaLOGO.png', 'Mishiro9.jpg',
           'Inuyama15.jpg', 'Srk-icon1.jpg', 'NoWorld头图背景窄长.png', 'Satousatou-icon2.jpg',
           '转圈再转个圈（全身立绘）.png', '虚研社：兰音（4.0）.png', '雪风军团Logo.png', '叶玖凉Ryou（展示图）.jpg',
           '月見夜兰（头部立绘）.png', '猫邮社：竹月芽-2022.png', 'JK Mao logo.png', 'HP member komame.png',
           'Kaguya Luna Tricolor Cross.png', '虚研社：木糖纯（初始立绘）.png', 'Logo fin22.png', '阿梓 头图.png',
           'MarySaionji 500x500(02).png', 'Karuta1.jpg', 'Aria头.jpg', '鶹鸝公式ver.png'}
exclude = {Page(source=cm, title="File:" + e).title() for e in exclude}


def find_image_links(page: Page):
    expanded = page.expand_text()
    images = {p.title() for p in page.imagelinks()}
    file_paths = re.findall("{{filepath:([^}]+)}}", expanded)
    images = set.union(images,
                       set(file_paths),
                       set(get_commons_links(expanded)))
    result = set()
    for image in images:
        p = Page(source=cm,
                 title="File:" + image if not re.search("[fF]ile:", image, re.IGNORECASE)
                 else image)
        try:
            result.add(p.title())
        except InvalidTitleError:
            pass
    return result.difference(exclude)


CONT_FILE = "vtuber_commons_cat_continue.txt"


def query_cats(files: Iterable[str]):
    result = []
    for sublist in itergroup(files, 50):
        url = "https://commons.moegirl.org.cn/api.php"
        response = requests.get(url, params={
            "action": 'query',
            'prop': 'categories',
            "cllimit": 500,
            'titles': "|".join(sublist),
            # 'clcategories': page.title(),
            'format': 'json'
        }).json()['query']['pages'].values()
        result.extend(response)
    return result


def query_templates_for_exceptions():
    gen = GeneratorFactory(site=mgp)
    gen.handle_arg("-ns:Template")
    gen.handle_arg("-catr:虚拟UP主导航模板")
    pages = gen.getCombinedGenerator(preload=False)
    images = set()
    for page in pages:
        print("Processing " + page.title())
        images.update(find_image_links(page))
        print(len(images))
        with open(get_data_path().joinpath("vtuber_template_images.txt"), "w") as f:
            f.write(str(images))
            f.flush()
    print(images)


def exclude_removed_pages():
    # text to process
    fin1 = open(get_data_path().joinpath("vtuber_commons_cat_result.txt"), "r")
    # modified list with potential deletions
    fin2 = open(get_data_path().joinpath("in2.txt"), "r")
    name_list = fin2.read()
    keep = True
    for line in fin1.readlines():
        s = re.search(r"\*\[\[(.+)]]", line)
        if "**" not in line and s is not None:
            page_title = s.group(1)
            keep = ("*[[" + page_title + "]]") in name_list
        if keep:
            print(line.strip())


def redo_excluded_files():
    lines = open(get_data_path().joinpath("in.txt"), "r").read().split("\n")
    out = open(get_data_path().joinpath("out.txt"), "w")
    for line in lines:
        fn = re.search(r"\[\[cm:File:([^|]+)\|", line)
        if fn and 'File:' + fn.group(1) in exclude:
            continue
        out.write(line + "\n")


def vtuber_commons_cat():
    gen = GeneratorFactory()
    gen.handle_arg("-ns:0")
    gen.handle_arg("-catr:虚拟UP主")
    pages = get_page_list(file_name="vtuber_commons_cat_pages.txt",
                          factory=gen.getCombinedGenerator(preload=False),
                          cont=get_continue_page(CONT_FILE),
                          site=mgp)
    for page in pages:
        files = find_image_links(page)
        output = ""
        if len(files) == 0:
            print("No images on " + page.title())
            continue
        response = query_cats(files)
        output += "*[[" + page.title() + "]]：" + "[[cm:Cat:" + page.title(with_ns=False) + "]]\n"
        for result in response:
            if 'categories' in result:
                cats = {c['title'].replace('Category:', '') for c in result['categories']}
            else:
                cats = set()
            cats.discard("原作者保留权利")
            if page.title() in cats:
                continue
            title_without_ns = result['title'].replace('File:', '')
            output += f"**[[cm:{result['title']}|{title_without_ns}]]" \
                      f"（{'、'.join(cats)}）\n"
        with open(get_data_path().joinpath("vtuber_commons_cat_result.txt"), "a") as f:
            f.write(output)
        save_continue_page(CONT_FILE, page.title())
