import re
from unittest import TestCase

from bots.isbn import treat_isbn


class TestIsbn(TestCase):
    def test_treat_isbn(self):
        text = "ISBN 978-490686622-X | {{ISBN|4718016015678}}"
        self.assertEqual("{{ISBN|978-490686622-X}} | {{ISBN|4718016015678}}",
                         treat_isbn(text))
        text = "ISBN 978-490686622-X | ISBN：4718016015678"
        self.assertEqual("{{ISBN|978-490686622-X}} | ISBN：{{ISBN|4718016015678|4718016015678}}",
                         treat_isbn(text))
        text = """|2018年8月10日
|ISBN978-4041050897
|-"""
        self.assertEqual("""|2018年8月10日
|{{ISBN|978-4041050897}}
|-""",
                         treat_isbn(text))

    def test_isbn_comments(self):
        text = "<!-- || ISBN978-4-7981-4287-494-->"
        self.assertEqual(
            '<!-- || {{ISBN|978-4-7981-4287-494}}-->',
            treat_isbn(text))


    def test_keep_isbn(self):
        texts = ["joijoifwjoiew", "ISBN", "ISBN 123啊", "|image=ISBN978-7-5581-8236-5.jpg",
                 "[[Special:网络书源/978-7-5366-9396-8|ISBN 978-7-5366-9396-8]]",
                 "https://www.editor.co.jp/press/ISBN/ISBN978-4-88888-933-9.htm",
                 "[https://google.com ISBN978-7-5366-9396-8]",
                 "{{jk|Something<ref>[https://book.kongfz.com/16761/896940001/ 第五册ISBN7-5386-0229-1/J·140]</ref>}}",
                 "|别号=乔乔、JOJO、乔斯达桑、大乔、大天使、{{黑幕|简纳桑·江斯特、简江<ref>来自早年吉林美术出版社《勇敢的斗士》（其中"
                 "[https://book.kongfz.com/16761/896940001/ 第五册ISBN7-5386-0229-1/J·140]、"
                 "[https://book.douban.com/subject/3939394/ 第八册ISBN9787538602296]）"
                 "的生草翻译，原因是为了把名字本土化，故意弄的中文谐音，迪奥的名字还被翻译成了狄奥。"
                 "（顺便一提该版本的实体书在某些网站上可以买到）</ref>}}、<del>面包超人<ref>指更換頭部<del>和DIO面包</del></ref>"
                 "</del>、{{胡话|猴面包树}}"]
        for t in texts:
            self.assertEqual(t, treat_isbn(t))

    def test_isbn_long(self):
        text = """{|class="wikitable" style="font-size: small;"
|-
!封面
!名称
!发售日期
!ISBN号
|-
|[[File:rst_N1.jpg|100px|left]]
|Re:Stage!第一卷
|2016年3月10日
|ISBN978-4041040645
|-
|[[File:rst_N2.jpg|100px|left]]
|Re:Stage!第二卷
|2017年1月26日
|ISBN978-4041050859
|-
|[[File:rst_N3.jpg|100px|left]]
|Re:Stage!第三卷
|2018年8月10日
|ISBN978-4041050897
|-
|}"""
        self.assertEqual("""{|class="wikitable" style="font-size: small;"
|-
!封面
!名称
!发售日期
!ISBN号
|-
|[[File:rst_N1.jpg|100px|left]]
|Re:Stage!第一卷
|2016年3月10日
|{{ISBN|978-4041040645}}
|-
|[[File:rst_N2.jpg|100px|left]]
|Re:Stage!第二卷
|2017年1月26日
|{{ISBN|978-4041050859}}
|-
|[[File:rst_N3.jpg|100px|left]]
|Re:Stage!第三卷
|2018年8月10日
|{{ISBN|978-4041050897}}
|-
|}""",
                         treat_isbn(text))
        text = """|1993年6月25日||ISBN 978-4-253-05434-8
|2009年9月14日||EAN 471-1552-44606-7
|-
!2
|1993年10月29日||ISBN 978-4-253-05435-5
|2009年10月1日||EAN 471-1552-44607-4
|-
!3
|1994年2月3日||ISBN 978-4-253-05436-2
|2009年10月15日||EAN 471-1552-44608-1
|-
!4
|1994年6月2日||ISBN 978-4-253-05437-9
|2009年10月30日||EAN 471-1552-44609-8
|-
!5
|1994年9月16日||ISBN 978-4-253-05438-6
|2009年11月12日||EAN 471-1552-44610-4
|-
!6
|1994年12月9日||ISBN 978-4-253-05439-3
|2009年11月30日||EAN 471-1552-44611-1
|-
!7
|1995年4月14日||ISBN 978-4-253-05440-9
|2009年12月16日||EAN 471-1552-44612-8
|-
!8
|1995年7月6日||ISBN 978-4-253-05441-6
|2010年1月5日||EAN 471-1552-44613-5
|-
!9
|1995年10月13日||ISBN 978-4-253-05442-3
|2010年1月15日||EAN 471-1552-44614-2
|-
!10
|1995年12月22日||ISBN 978-4-253-05443-0
|2010年2月4日||EAN 471-1552-44615-9
|-
!11
|1996年5月17日||ISBN 978-4-253-05444-7
|2010年3月9日||EAN 471-1552-44616-6
|-
!12
|1996年9月6日||ISBN 978-4-253-05445-4
|2010年4月22日||EAN 471-1552-44617-3
|-
!13
|1996年12月11日||ISBN 978-4-253-05446-1
|2010年6月12日||EAN 471-1552-44618-0
|-
!14
|1997年3月14日||ISBN 978-4-253-05447-8
|2010年7月6日||EAN 471-1552-44619-7
|-
!15
|1997年7月18日||ISBN 978-4-253-05448-5
|2010年8月25日||EAN 471-1552-44620-3
|-
!16
|1997年12月5日||ISBN 978-4-253-05449-2
|2010年9月29日||EAN 471-3469-35496-1
|-
!17
|1998年3月6日||ISBN 978-4-253-05450-8
|2010年10月19日||EAN 471-3469-35497-8
|-
!18
|1998年7月4日||ISBN 978-4-253-05451-5
|2010年11月9日||EAN 471-3469-35498-5
|-
!19
|1998年10月16日||ISBN 978-4-253-05452-2
|2010年12月1日||EAN 471-3469-35499-2
|-
!20
|1999年1月8日||ISBN 978-4-253-05453-9
|2010年12月31日||EAN 471-3469-35500-5
|-
!21
|1999年4月8日||ISBN 978-4-253-05751-6
|2011年3月8日||EAN 471-3469-35827-3
|-
!22
|1999年7月15日||ISBN 978-4-253-05752-3
|2011年3月31日||EAN 471-3469-35950-8
|-
!23
|1999年11月4日||ISBN 978-4-253-05753-0
|2011年5月10日||EAN 471-6814-19030-6
|-
!24
|2000年2月24日||ISBN 978-4-253-05754-7
|2011年5月24日||EAN 471-6814-19090-0
|-
!25
|2000年6月15日||ISBN 978-4-253-05755-4
|2011年6月28日||EAN 471-6814-19187-7
|-
!26
|2000年10月12日||ISBN 978-4-253-05756-1
|2011年8月17日||EAN 471-6814-19188-4
|-
!27
|2001年2月8日||ISBN 978-4-253-05757-8
|2011年8月24日||EAN 471-6814-19301-7
|-
!28
|2001年6月14日||ISBN 978-4-253-05758-5
|2011年9月6日||EAN 471-6814-19313-0
|-
!29
|2001年10月11日||ISBN 978-4-253-05759-2
|2011年9月20日||EAN 471-6814-19370-3
|-
!30
|2002年2月21日||ISBN 978-4-253-05760-8
|2011年10月5日||EAN 471-6814-19423-6
|-
!31
|2002年5月2日||ISBN 978-4-253-05762-2
|2011年11月4日||EAN 471-6814-19485-4
|}

; 元祖！浦安铁筋家族
{| class=wikitable style="font-size:small;"
!rowspan="2"|册数
!colspan="2"|秋田书店
!colspan="2"|长鸿出版社
|-
!发售日期!!ISBN!!发售日期!!EAN
|-
!1
|2002年9月5日||ISBN 978-4-253-20301-2
|2002年12月20日||EAN 471-0765-17158-2
|-
!2
|2003年1月23日||ISBN 978-4-253-20302-9
|2003年5月5日||EAN 471-0765-17517-7
|-
!3
|2003年4月24日||ISBN 978-4-253-20303-6
|2003年8月7日||EAN 471-0765-17647-1
|-
!4
|2003年8月21日||ISBN 978-4-253-20304-3
|2003年10月30日||EAN 471-0765-17987-8
|-
!5
|2003年12月25日||ISBN 978-4-253-20305-0
|2004年1月29日||EAN 471-0765-18200-7
|-
!6
|2004年4月28日||ISBN 978-4-253-20306-7
|2004年6月9日||EAN 471-0765-18561-9
|-
!7
|2004年8月26日||ISBN 978-4-253-20307-4
|2004年10月22日||EAN 471-0765-18926-6
|-
!8
|2004年11月11日||ISBN 978-4-253-20308-1
|2005年2月18日||EAN 471-0765-19236-5
|-
!9
|2005年3月8日||ISBN 978-4-253-20309-8
|2005年6月23日||EAN 471-0765-19596-0
|-
!10
|2005年6月8日||ISBN 978-4-253-20310-4
|2005年8月17日||EAN 471-0765-19800-8
|-
!11
|2005年10月8日||ISBN 978-4-253-20311-1
|2006年2月10日||EAN 471-0765-20229-3
|-
!12
|2006年2月8日||ISBN 978-4-253-20312-8
|2006年5月15日||EAN 471-0765-20487-7
|-
!13
|2006年6月8日||ISBN 978-4-253-20313-5
|2006年9月23日||EAN 471-0765-20854-7
|-
!14
|2006年9月8日||ISBN 978-4-253-20314-2
|2007年1月3日||EAN 471-0765-21116-5
|-
!15
|2007年1月9日||ISBN 978-4-253-20315-9
|2007年4月18日||EAN 471-0765-21066-3
|-
!16
|2007年5月8日||ISBN 978-4-253-20316-6
|2007年7月24日||EAN 471-0765-21565-1
|-
!17
|2007年9月7日||ISBN 978-4-253-20317-3
|2007年11月21日||EAN 471-0765-21927-7
|-
!18
|2007年12月7日||ISBN 978-4-253-20318-0
|2008年1月19日||EAN 471-2805-82149-5
|-
!19
|2008年5月8日||ISBN 978-4-253-20319-7
|2008年7月11日||EAN 471-2805-82557-8
|-
!20
|2008年8月8日||ISBN 978-4-253-20320-3
|2008年10月15日||EAN 471-2805-82790-9
|-
!21
|2008年11月7日||ISBN 978-4-253-20321-0
|2008年12月22日||EAN 471-1552-44015-7
|-
!22
|2009年3月6日||ISBN 978-4-253-20322-7
|2009年4月20日||EAN 471-1552-44279-3
|-
!23
|2009年7月8日||ISBN 978-4-253-20323-4
|2009年8月15日||EAN 471-1552-44555-8
|-
!24
|2009年10月8日||ISBN 978-4-253-20324-1
|2009年11月24日||EAN 471-1552-44825-2
|-
!25
|2010年1月8日||ISBN 978-4-253-20325-8
|2010年3月4日||EAN 471-3469-35043-7
|-
!26
|2010年6月8日||ISBN 978-4-253-20326-5
|2010年8月3日||EAN 471-3469-35394-0
|-
!27
|2010年11月8日||ISBN 978-4-253-20327-2
|2011年1月26日||EAN 471-3469-35866-2
|-
!28
|2011年1月7日||ISBN 978-4-253-20328-9
|2011年4月16日||EAN 471-3469-35995-9
|}"""
        self.assertEqual(re.sub(r"ISBN ([\d-]+)", r"{{ISBN|\1}}", text),
                         treat_isbn(text))
