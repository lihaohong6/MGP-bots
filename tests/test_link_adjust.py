from unittest import TestCase

from bots.link_adjust import process_text_bb, process_text_yt, treat_links


class TestLinkAdjust(TestCase):
    def test_dead_link_remove(self):
        url = "[https://www.bilibili.com/video/BV1bW4y1q79d?spm_id_from=1 链接] \n{{死链|bot=Bhsd-bot|date=123}}AAA"
        self.assertEqual(
            "[https://www.bilibili.com/video/BV1bW4y1q79d 链接]AAA",
            process_text_bb(url))
        url = "https://www.bilibili.com/video/BV1bW4y1q79d?spm_id_from=1{{死链|date=abc|bot=Bhsd-bot}}"
        self.assertEqual(
            "https://www.bilibili.com/video/BV1bW4y1q79d",
            process_text_bb(url)
        )
        url = "[https://youtu.be/h-FccHqdLV0?t=81 油管视频]{{失效連結|bot=Bhsd-bot}}"
        self.assertEqual(
            "[https://www.youtube.com/watch?v=h-FccHqdLV0&t=81 油管视频]",
            process_text_yt(url)
        )
        url = "https://b23.tv/t8BP0j {{失效链接|bot=Bhsd-bot}}"
        self.assertEqual(
            "https://www.bilibili.com/video/BV1AV411h7jb",
            process_text_bb(url)
        )

    def test_dead_link_keep(self):
        # 没有bot=Bhsd-bot
        url = "[https://www.bilibili.com/video/BV1bW4y1q79d?spm_id_from=1 链接]{{死链|date=123}}AAA"
        self.assertEqual("[https://www.bilibili.com/video/BV1bW4y1q79d 链接]{{死链|date=123}}AAA",
                         process_text_bb(url))
        url = "https://youtu.be/h-FccHqdLV0?t=81 {{死链|date=123}}"
        self.assertEqual("https://www.youtube.com/watch?v=h-FccHqdLV0&t=81 {{死链|date=123}}",
                         process_text_yt(url))
        # 链接没有变化
        url = "[https://www.bilibili.com/video/BV1bW4y1q79d 链接]{{死链|bot=Bhsd-bot|date=123}}"
        self.assertEqual(url, process_text_bb(url))
        url = "https://www.youtube.com/watch?v=h-FccHqdLV0 {{死链|bot=Bhsd-bot|date=123}}"
        self.assertEqual(url, process_text_yt(url))
        url = "https://b23.tv/jofwovjowi2 {{失效链接|bot=Bhsd-bot}}"
        self.assertEqual(url, process_text_bb(url))

    def test_process_text_bb(self):
        # 去除t=1和外的所有参数
        url = "https://www.bilibili.com/video/BV1bW4y1q79d?" \
              "spm_id_from=333.851.b_7265636f6d6d656e64.1&" \
              "t=1&vd_source=4283250c27f32cce49b24b0f6e6c149d&p=1"
        self.assertEqual(
            "https://www.bilibili.com/video/BV1bW4y1q79d?t=1",
            process_text_bb(url))
        # t=1, p=3，因此p不会被去掉
        url = "https://www.bilibili.com/video/BV1bW4y1q79d?" \
              "spm_id_from=333.851.b_7265636f6d6d656e64.1&" \
              "t=1&vd_source=4283250c27f32cce49b24b0f6e6c149d&p=3"
        self.assertEqual(
            "https://www.bilibili.com/video/BV1bW4y1q79d?t=1&p=3",
            process_text_bb(url))
        # 直播
        url = "https://live.bilibili.com/21996804?broadcast_type=0&is_room_feed=1&spm_id_from=333.999.0.0"
        self.assertEqual("https://live.bilibili.com/21996804",
                         process_text_bb(url))
        # 动态
        url = "https://t.bilibili.com/702110621963911221?spm_id_from=444.41.0.0"
        self.assertEqual("https://t.bilibili.com/702110621963911221",
                         process_text_bb(url))
        # 专栏
        url = "https://www.bilibili.com/read/cv3434476?from=search&spm_id_from=333.337.0.0"
        self.assertEqual("https://www.bilibili.com/read/cv3434476",
                         process_text_bb(url))
        url = "https://www.bilibili.com/read/mobile?id=4574032"
        self.assertEqual("https://www.bilibili.com/read/cv4574032",
                         process_text_bb(url))
        url = "https://www.bilibili.com/read/mobile/10424161"
        self.assertEqual("https://www.bilibili.com/read/cv10424161",
                         process_text_bb(url))
        # 空间
        url = "https://space.bilibili.com/39260796/article?from=search"
        self.assertEqual("https://space.bilibili.com/39260796/article",
                         process_text_bb(url))
        # 处理b23.tv
        # 视频
        url = "https://b23.tv/t8BP0j"
        self.assertEqual("https://www.bilibili.com/video/BV1AV411h7jb",
                         process_text_bb(url))
        url = "https://b23.tv/jf8kgOH"
        self.assertEqual("https://www.bilibili.com/video/BV1tY4y1s7JE",
                         process_text_bb(url))
        url = "https://b23.tv/26FWI5p"
        self.assertEqual("https://www.bilibili.com/video/BV19y4y1Y7m3/?p=9",
                         process_text_bb(url))
        # 空间
        url = "https://b23.tv/cYG0K8"
        self.assertEqual("https://space.bilibili.com/674746763",
                         process_text_bb(url))
        url = "https://b23.tv/uD6S24"
        self.assertEqual("https://space.bilibili.com/2023988132",
                         process_text_bb(url))
        # 会员购
        url = "https://mall.bilibili.com/detail.html?&itemsId=10040825&jumpLinkType=0&msource=link&noTitleBar=1" \
              "&share_medium=android&share_plat=android&share_source=COPY&share_tag=s_i&timestamp=1636345640" \
              "&unique_k=XlSwmO#noReffer=true&goFrom=na"
        self.assertEqual("https://mall.bilibili.com/detail.html?itemsId=10040825#noReffer=true&goFrom=na",
                         process_text_bb(url))

    def test_process_text_yt_no_change(self):
        # 无更改
        url = "https://www.youtube.com/watch?v=k9jAlYmNK5A&t=12s"
        self.assertEqual(url, process_text_yt(url))
        url = "2015年8月31日发布首个[https://www.youtube.com/watch?v=MILDduR_k9c 试听曲]"
        self.assertEqual(url, process_text_yt(url))

    def test_process_text_yt_expand(self):
        # 展开youtu.be
        url = "https://youtu.be/h-FccHqdLV0?t=81"
        self.assertEqual("https://www.youtube.com/watch?v=h-FccHqdLV0&t=81",
                         process_text_yt(url))
        url = "https://youtu.be/jA8M_oYpODo"
        self.assertEqual("https://www.youtube.com/watch?v=jA8M_oYpODo",
                         process_text_yt(url))

    def test_process_text_yt_remove(self):
        # YouTube链接的无效参数
        url = "https://youtube.com/watch?feature=youtu.be&v=t-ES9KW_Ij8"
        self.assertEqual("https://youtube.com/watch?v=t-ES9KW_Ij8",
                         process_text_yt(url))
        url = "https://www.youtube.com/watch?v=be8wqUqDhFU&feature=youtu.be"
        self.assertEqual("https://www.youtube.com/watch?v=be8wqUqDhFU",
                         process_text_yt(url))

    def test_keep(self):
        urls = ["https://www.bilibili.com/video/BV1bW4y1q79d",
                "https://www.bilibili.com/video/BV1bW4y1q79d?t=123/"
                "https://www.bilibili.com/festival/2022bnj?bvid=BV1tR4y1j7aZ",
                "https://space.bilibili.com/562197/video?keyword=中国boy解说",
                "https://space.bilibili.com/525455041/channel/collectiondetail?sid=125609 ",
                "https://www.youtube.com/watch?v=n8PNy1EvsB4&list=PLPUGXakMkjRH0PwmVsFqWlBqHDq1yLurm",
                "https://www.bilibili.com/medialist/play/103835?business=space_series&business_id=901366&desc=1",
                "youtu.be<nowiki>/</nowiki>n8PNy1EvsB4",
                'https://b23.tv/n92He6w']
        for u in urls:
            self.assertEqual(u, treat_links(u))

    def test_special(self):
        url = "b站直播间的链接是https://live.bilibili.com/21996804?broadcast_type=0&is_room_feed=1哦"
        self.assertEqual("b站直播间的链接是https://live.bilibili.com/21996804哦",
                         process_text_bb(url))
        url = "[https://live.bilibili.com/21996804?broadcast_type=0&is_room_feed=1{{lj|あああ}}]"
        self.assertEqual("[https://live.bilibili.com/21996804{{lj|あああ}}]",
                         process_text_bb(url))
        url = "{{黑幕|https://b23.tv/cYG0K8}}"
        self.assertEqual("{{黑幕|https://space.bilibili.com/674746763}}",
                         process_text_bb(url))

    def test_bugs(self):
        # FIXME: this test does not pass
        # url = "https://b23.tv/jsuQZf3"
        # self.assertEqual("https://www.bilibili.com/read/cv20732933",
        #                  process_text_bb(url))
        # test buvid and upid params
        url = "https://b23.tv/HNeNlxa"
        self.assertEqual("https://www.bilibili.com/video/BV1Pe411c7oL",
                         process_text_bb(url))
        # test additional params
        url = "https://b23.tv/QP7RG2Q"
        self.assertEqual("https://t.bilibili.com/715983168805535747",
                         process_text_bb(url))

    def test_long(self):
        expected = """**在练自由搏击（{{lj|キックボクシング}}）{{黑幕|本想瘦腿，结果上半身变瘦}}<ref>[https://www.bilibili.com/video/BV1Jz4y1U7BA 【切片中字】胸部装甲被削弱的爱美社长？]</ref>

母亲：樱井文绘<ref>[https://www.bilibili.com/video/BV1C3411k7s9]</ref>

相关内容可见[https://www.bilibili.com/video/BV1Yg411y7xN 《深空之眼》拾梦绘卷|最优秀的女仆]

2022年8月19日[[HIKARI FIELD]]宣布将制作国际中文版，并公开了中文版开场动画<ref>{{Cite web|title=《苍之彼方的四重奏EXTRA2》国际中文版制作决定！|url=https://t.bilibili.com/696063187661881477|accessdate=2022-08-19|date=2022-08-19|language=zh}}</ref>，预计于2022年内发售。

<ref>https://www.bilibili.com/video/BV1Us411v78x?t=10&p=5</ref>

2015年8月31日发布首个[https://www.youtube.com/watch?v=MILDduR_k9c 试听曲]

** 4月10日开始与[[佐佐木未来]]、[[伊藤彩沙]]以“'''声优三姐妹 TeamY'''（[https://www.youtube.com/channel/UCtD8UMFAgAUn7sGGPK5IvAA {{lj|声优三姊妹『チームY』}}]）”组合名义Youtuber出道。

PS4上有玩《东方深秘录》。<ref>东方station 特别嘉宾上坂堇 https://www.bilibili.com/video/BV19E41157qu?t=220</ref>

车重1151KG 推重比126kg·m[https://www.bilibili.com/read/cv3434476]

[https://www.bilibili.com/video/BV1Lt4y1L7Je]

* 中国版官网：https://bml.bilibili.com/sp
* 海外版官网：https://www.bmlsp.bilibili.com/ですわ
<references/>"""

        original = """**在练自由搏击（{{lj|キックボクシング}}）{{黑幕|本想瘦腿，结果上半身变瘦}}<ref>[https://b23.tv/iMhxQi 【切片中字】胸部装甲被削弱的爱美社长？]</ref>

母亲：樱井文绘<ref>[https://b23.tv/zcklGO]</ref>

相关内容可见[https://www.bilibili.com/video/BV1Yg411y7xN?spm_id_from=444.42.list.card_archive.click 《深空之眼》拾梦绘卷|最优秀的女仆]

2022年8月19日[[HIKARI FIELD]]宣布将制作国际中文版，并公开了中文版开场动画<ref>{{Cite web|title=《苍之彼方的四重奏EXTRA2》国际中文版制作决定！|url=https://t.bilibili.com/696063187661881477?spm_id_from=333.999.0.0|accessdate=2022-08-19|date=2022-08-19|language=zh}}</ref>，预计于2022年内发售。

<ref>https://www.bilibili.com/video/BV1Us411v78x?spm_id_from=333.337.search-card.all.click&vd_source=99b3fa924294d33ca365ef499286ea01&t=10&p=5</ref>

2015年8月31日发布首个[https://www.youtube.com/watch?v=MILDduR_k9c 试听曲]

** 4月10日开始与[[佐佐木未来]]、[[伊藤彩沙]]以“'''声优三姐妹 TeamY'''（[https://www.youtube.com/channel/UCtD8UMFAgAUn7sGGPK5IvAA {{lj|声优三姊妹『チームY』}}]）”组合名义Youtuber出道。

PS4上有玩《东方深秘录》。<ref>东方station 特别嘉宾上坂堇 https://www.bilibili.com/video/BV19E41157qu?t=220</ref>

车重1151KG 推重比126kg·m[https://www.bilibili.com/read/cv3434476?from=search&spm_id_from=333.337.0.0]

[https://www.bilibili.com/video/BV1Lt4y1L7Je/?spm_id_from=333.788.recommend_more_video.-1&vd_source=52e727c44f740afa0d193be4aadcd11c]

* 中国版官网：https://bml.bilibili.com/sp?spm_id_from=333.999.rich-text.link.click
* 海外版官网：https://www.bmlsp.bilibili.com/ですわ
<references/>"""
        self.assertEqual(expected, treat_links(original))
