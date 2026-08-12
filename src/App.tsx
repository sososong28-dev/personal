import { AnimatePresence, motion, type Transition } from 'framer-motion'
import {
  ArrowUpRight,
  BrainCircuit,
  CalendarDays,
  CheckCircle2,
  FileText,
  Layers3,
  LockKeyhole,
  MapPin,
  Menu,
  MessageCircle,
  PackageCheck,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import * as THREE from 'three'
import { type ReactNode, useEffect, useRef, useState } from 'react'
import nelsonHeroCharacter from '../static/nelson-hero-character.png'
import kefumeiBrandLineup from '../static/projects/kefumei/assets/brand-lineup.jpg'
import kefumeiCampaignRecap from '../static/projects/kefumei/assets/campaign-recap.jpg'
import kefumeiCelebrityGrid from '../static/projects/kefumei/assets/celebrity-grid.jpg'
import kefumeiClinicalHandCase from '../static/projects/kefumei/assets/clinical-hand-case.jpg'
import kefumeiDeviceSheet from '../static/projects/kefumei/assets/device-sheet.jpg'
import kefumeiIpCampaign from '../static/projects/kefumei/assets/ip-campaign.jpg'
import kefumeiKolEducationMatrix from '../static/projects/kefumei/assets/kol-education-matrix.jpg'
import kefumeiMedicalChannelMap from '../static/projects/kefumei/assets/medical-channel-map.jpg'
import kefumeiO2oChannel from '../static/projects/kefumei/assets/o2o-channel.jpg'
import kefumeiRetailDisplay from '../static/projects/kefumei/assets/retail-display.jpg'
import kefumeiThreeProductSystem from '../static/projects/kefumei/assets/three-product-system.jpg'
import yikougegeContentMatrix from '../static/projects/yikougege/assets/content-matrix.jpg'
import yikougegeEcommerceGrid from '../static/projects/yikougege/assets/ecommerce-grid.jpg'
import yikougegeLiveCommerce from '../static/projects/yikougege/assets/live-commerce.jpg'
import yikougegeMediaPlacement from '../static/projects/yikougege/assets/media-placement.jpg'
import yikougegePackagingSystem from '../static/projects/yikougege/assets/packaging-system.jpg'
import yikougegeProductFamily from '../static/projects/yikougege/assets/product-family.jpg'
import yikougegeProductIteration from '../static/projects/yikougege/assets/product-iteration.jpg'
import yikougegeRedPacketSystem from '../static/projects/yikougege/assets/red-packet-system.jpg'
import yikougegeRetailDisplay from '../static/projects/yikougege/assets/retail-display.jpg'
import yikougegeSportsScene from '../static/projects/yikougege/assets/sports-scene.jpg'
import yikougegeTradeShow from '../static/projects/yikougege/assets/trade-show.jpg'
import yikougegeTrainingRoom from '../static/projects/yikougege/assets/training-room.jpg'
import jikex001ConsumerHa from '../static/projects/jikex001/assets/consumer-survey-ha.png'
import jikex001ConsumerPainpoints from '../static/projects/jikex001/assets/consumer-survey-painpoints.png'
import jikex001NamingSurvey from '../static/projects/jikex001/assets/naming-survey.png'
import jikex001ProductHouse from '../static/projects/jikex001/assets/product-house.png'

const ease: Transition['ease'] = [0.22, 1, 0.36, 1]

const navItems = [
  { label: '个人介绍', href: '#about' },
  { label: '经历时间线', href: '#timeline' },
  { label: '能力板块', href: '#capabilities' },
  { label: '项目作品', href: '#projects' },
  { label: '联系方式', href: '#contact' },
]

const timelineItems = [
  {
    id: 'hongkong',
    period: '2017 - 2022',
    city: '香港',
    title: '市场一线',
    subtitle: '从真实业务现场理解用户、渠道和销售场景。',
    summary:
      '第一份正式工作让我进入市场一线。我开始理解用户如何判断一个产品，也开始意识到表达、信任和落地能力会直接影响项目能不能被接受。',
    tags: ['市场感知', '用户反馈', '销售场景', '一线沟通'],
  },
  {
    id: 'shenzhen',
    period: '2022 - 2025',
    city: '深圳',
    title: '独立项目线',
    subtitle: '从市场视角走向独立项目推进和工具协作。',
    summary:
      '来到深圳后，我开始进入更独立的项目推进环境。这一阶段让我训练自己拆解需求、整理资料、推动协作，并把想法推进成可以交付的结果。',
    tags: ['项目推进', '任务拆解', '工具使用', '结果交付'],
  },
  {
    id: 'beijing',
    period: '2025 - 至今',
    city: '北京',
    title: '产品中心',
    subtitle: '把市场、内容、项目和产品连接起来。',
    summary:
      '现在我更靠近产品中心，开始系统地看待用户、需求、内容、产品和结果之间的关系。相比单点执行，我更关注完整链路和长期沉淀。',
    tags: ['产品视角', '内容结构', '系统思维', '经验沉淀'],
  },
]

const projects = [
  {
    id: 'jikex001',
    index: '01',
    name: '001 产品开发与 AI 营销创新',
    type: '产品定位 / AI 营销验证',
    description:
      '从使用场景里的真实打断点切入，重建 001 的产品开发逻辑，并用 AI 验证低打扰、私密、互动式传播方式。',
    role: '产品逻辑梳理 / 卖点定义 / 竞品差异 / AI 营销验证',
    cover: jikex001ProductHouse,
    images: [jikex001ConsumerPainpoints, jikex001ConsumerHa, jikex001NamingSurvey],
    tags: ['产品屋', '低打扰', '双润滑', 'AI营销'],
    detailUrl: '/me/projects/001',
  },
  {
    id: 'yikougege',
    index: '02',
    name: '益口葛葛',
    type: '品牌项目 / 项目介绍资料',
    description:
      '围绕品牌定位、产品表达和项目介绍资料，重新整理成更适合展示和阅读的项目案例。',
    role: '资料整理 / 内容理解 / 页面呈现 / 项目复盘',
    cover: yikougegeProductFamily,
    images: [yikougegePackagingSystem, yikougegeContentMatrix, yikougegeRetailDisplay],
    tags: ['品牌项目', '内容呈现', '项目资料'],
    detailUrl: '/me/projects/yikougege',
  },
  {
    id: 'kefumei',
    index: '03',
    name: '可复美',
    type: '产品培训 / 产品内容资料',
    description:
      '围绕产品知识、功效表达和培训内容，重新整理成更清晰、更适合展示的产品资料案例。',
    role: '产品资料整理 / 培训内容理解 / 信息重构',
    cover: kefumeiBrandLineup,
    images: [kefumeiThreeProductSystem, kefumeiKolEducationMatrix, kefumeiRetailDisplay],
    tags: ['产品培训', '内容整理', '产品表达'],
    detailUrl: '/me/projects/kefumei',
  },
]

const capabilitySections = [
  {
    id: 'product',
    index: '01',
    title: '产品板块',
    eyebrow: 'Product',
    summary: '从用户痛点、竞品差异和产品屋出发，把机会收束成可立项、可验证、可表达的产品逻辑。',
    tags: ['用户洞察', '产品屋', '卖点定义'],
    href: '/me/capabilities/product',
  },
  {
    id: 'gtm',
    index: '02',
    title: 'GTM 板块',
    eyebrow: 'Go-To-Market',
    summary: '把新品推进拆成渠道、内容、节点、责任人和复盘口径，减少跨部门协同里的信息断层。',
    tags: ['渠道承接', '内容转译', '复盘机制'],
    href: '/me/capabilities/gtm',
  },
  {
    id: 'merchandise',
    index: '03',
    title: '商品板块',
    eyebrow: 'Merchandise',
    summary: '围绕货盘、价格、库存、平台规则和经营数据，支持选品、上新、控价和复盘判断。',
    tags: ['货盘结构', '价格判断', '经营复盘'],
    href: '/me/capabilities/merchandise',
  },
]

const capabilityDetails = {
  product: {
    eyebrow: 'Product Capability',
    title: '产品板块',
    intro: '这个板块不展示“我会做产品”的泛能力，而是展示如何从用户语言、竞品边界和业务目标里，做出可被组织执行的产品判断。',
    thesis: '核心价值：把模糊机会压成可验证的产品逻辑。',
    stages: [
      ['问题识别', '先定义用户真实阻碍，而不是直接比较参数、概念或竞品话术。'],
      ['判断形成', '用用户证据、竞品边界、业务资源和品牌表达共同决定产品方向。'],
      ['结构拆解', '通过 POP / POD / RTB、产品屋和测试方向，把判断拆成可执行模块。'],
      ['业务支持', '让研发、包装、详情页、内容和销售能围绕同一套产品逻辑协同。'],
      ['复制能力', '同一方法可迁移到健康个护、快消、两性健康和医学修护类产品。'],
    ],
    examples: ['001 产品开发与 AI 营销创新', '可复美产品培训资料重组', '益口葛葛产品组合表达'],
  },
  gtm: {
    eyebrow: 'GTM Capability',
    title: 'GTM 板块',
    intro: '这个板块强调从“把东西做出来”到“让市场接得住”。重点不是活动包装，而是渠道、内容、节点、责任和复盘口径的同步。',
    thesis: '核心价值：把新品上市从部门动作变成同一条业务链路。',
    stages: [
      ['问题识别', '新品推进常卡在口径不一致：渠道要卖点，内容要素材，商品要货盘，管理层要结果。'],
      ['判断形成', '先确认产品适合哪个渠道、哪个人群、哪个价格带、哪个内容表达。'],
      ['结构拆解', '拆成渠道入口、素材矩阵、培训话术、上新节点、数据复盘和风险清单。'],
      ['业务支持', '帮助销售、运营、内容、电商和管理层围绕同一套上市节奏行动。'],
      ['复制能力', '适合新消费、健康个护、实体产品和需要渠道协同的增长型公司。'],
    ],
    examples: ['益口葛葛渠道动销资料', '可复美 O2O 与门店承接', '001 AI 互动营销验证'],
  },
  merchandise: {
    eyebrow: 'Merchandise Capability',
    title: '商品板块',
    intro: '这个板块面向经营判断：不是只看某个产品好不好，而是看货盘、库存、价格、平台规则和数据落差如何影响业务结果。',
    thesis: '核心价值：把商品动作和经营结果放在同一张图里判断。',
    stages: [
      ['问题识别', '商品问题往往不是单个 SKU 的问题，而是货盘结构、价格带、库存周期和渠道规则叠加。'],
      ['判断形成', '结合市场需求、竞品价格、平台限制、库存状态和渠道反馈，判断该加码、提效还是止损。'],
      ['结构拆解', '拆成货盘层级、价格策略、上新节奏、库存风险、控价串货和复盘指标。'],
      ['业务支持', '支持商品 BP、渠道负责人、运营和管理层快速看到问题位置和下一步动作。'],
      ['复制能力', '可迁移到快消、个护、电商平台和线下渠道的日常经营复盘。'],
    ],
    examples: ['渠道动销货盘会议复盘', '年度复盘结构：通货 / 大日期 / 控价串货', 'UDI / 六九码规则拆解'],
  },
}

const insightPages = {
  radar: {
    eyebrow: 'Industry Radar',
    title: '行业雷达',
    intro: '行业雷达不放在首页第一位，而是在独立页面里展示持续观察市场的能力：用本地数据库沉淀竞品、品牌、平台、监管、投放和用户测评线索。',
    thesis: '核心价值：帮助企业更早看见竞争动作、价格变化、渠道机会和风险信号。',
    stages: [
      ['信息来源', '覆盖计生/两性健康、医药、美妆、AI 等赛道，沉淀新闻、测评、平台、品牌和监管信息。'],
      ['筛选逻辑', '不是简单存链接，而是按行业、品牌、平台、品类、主题和报告价值做归类。'],
      ['AI 总结', '把长信息转成可读摘要，方便快速判断是否需要进入产品、GTM 或商品复盘。'],
      ['业务转化', '将情报转为竞品差异、卖点边界、价格判断、投放观察和选题素材。'],
      ['对外价值', '向高管和投资者证明：判断不是临时灵感，而是有持续信息系统支撑。'],
    ],
    examples: ['竞品情报库', '每日简报', '按日归档', 'AI 结构化摘要'],
  },
  methodology: {
    eyebrow: 'Methodology',
    title: '方法论资产',
    intro: '方法论资产用于解释我如何工作：把真实工作复盘、产品案例、AI 工具和数据库沉淀，转成可复用的判断框架。',
    thesis: '核心价值：让经验不只停留在个人脑子里，而是变成组织可复用的结构。',
    stages: [
      ['产品屋', '用底层需求、中层价值、顶层表达，把产品机会从口号压成结构。'],
      ['数据落差复盘', '看需求、投放、ROI、品类角色之间是否协同，避免报喜式复盘。'],
      ['GTM 协同', '把政策、节点、责任人、平台规则和数据口径拆开管理。'],
      ['AI 工作流', '录音、逐字稿、个人感悟、选题、日报、案例和网站之间形成生产链。'],
      ['个人产品化', '像定义产品一样定义自己的岗位、价格带、差异化能力和案例资产。'],
    ],
    examples: ['产品屋方法论', '复盘不是报喜而是寻找数据落差', '录音到知识库工作流', '个人求职规划独立版'],
  },
}

const logicSteps = [
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: '问题识别',
    text: '同类产品常围绕薄度、成分、刺激感做竞争，但这些卖点容易被追平，也不一定解决真实体验里的中断。',
  },
  {
    icon: <Layers3 className="h-5 w-5" />,
    title: '产品屋逻辑',
    text: '用底层需求、中层价值、顶层表达讲清楚产品机会，而不是直接堆参数和口号。',
  },
  {
    icon: <BrainCircuit className="h-5 w-5" />,
    title: 'AI 营销验证',
    text: '把用户情绪、私密沟通和产品卖点连接起来，验证更轻、更低压力的互动式传播入口。',
  },
]

const aiMarketing = [
  '用 AI 生成低压力沟通话术，降低私密产品的表达尴尬。',
  '把用户情绪、场景和产品卖点连接成互动式内容，而不是硬广推销。',
  '先验证轻量 demo：NFC 私密确认卡、匿名情绪同步、场景化建议。',
  '沉淀用户反馈摘要，反向修正卖点、内容脚本和页面表达。',
]

const developmentStages = [
  {
    step: '01',
    title: '调研',
    subtitle: '从真实痛点出发',
    text: '整合 499 条使用后证据、323 条购买前搜索意图和公开评论，确认用户不只要薄，还要润、舒服、安心。',
  },
  {
    step: '02',
    title: '验证',
    subtitle: '问卷与命名测试',
    text: '145 人消费者问卷验证润滑持久、超薄无感、材质安全；53 人名称调研比较水润、潮涌、潮水、玻尿酸0感等方向。',
  },
  {
    step: '03',
    title: '立项',
    subtitle: '产品屋收束',
    text: '用水性聚氨酯 001 贴肤基底和重组玻尿酸双层稳态润滑体系，把低打扰、有效润滑和过程稳定落到产品结构。',
  },
  {
    step: '04',
    title: '实现',
    subtitle: '产品、包装、详情页',
    text: '把薄感贴近、玻尿酸顺滑、水润不断拆成包装正面、详情页首屏、科学机制页和 RTB 测试方向。',
  },
  {
    step: '05',
    title: '营销计划',
    subtitle: '场景传播 + AI 互动验证',
    text: '用低打扰、私密、互动式入口承接沟通场景，验证 AI 在话术生成、情绪同步、场景化建议和反馈沉淀中的价值。',
  },
]

const evidenceCards = [
  { value: '499', label: '使用后证据', note: '评论、公开样本与用户原话' },
  { value: '323', label: '购买前搜索意图', note: '抖音、京东、天猫热词' },
  { value: '145', label: '消费者问卷', note: '购买因素、成分、价格带验证' },
  { value: '53', label: '名称调研', note: '水润、潮涌、潮水、即刻等方向' },
]

const projectImages = [
  {
    src: jikex001ProductHouse,
    title: '产品屋',
    text: '潮水001 = 水性聚氨酯001贴肤基底 + 重组玻尿酸双层稳态润滑体系。',
  },
  {
    src: jikex001ConsumerPainpoints,
    title: '消费者问卷：痛点与成分偏好',
    text: '润滑持久不干、超薄无感、材质安全是关键购买因素；玻尿酸添加意愿达到 90.34%。',
  },
  {
    src: jikex001NamingSurvey,
    title: '新品名称调研',
    text: '水润001理解成本最低，潮涌001更有新品感；即刻/潮水等命名需要结合最终业务版本确认。',
  },
]

const yikougegeStages = [
  {
    step: '01',
    title: '资料整理',
    subtitle: '把品牌资料拆成可讲清的结构',
    text: '从产品家族、包装系统、内容矩阵、渠道动销和展会素材中抽出主线，先建立项目资料目录。',
  },
  {
    step: '02',
    title: '产品表达',
    subtitle: '从 SKU 到产品组合',
    text: '把单个产品信息整理为产品家族、使用场景和渠道展示，让项目不是散乱图片，而是有产品系统。',
  },
  {
    step: '03',
    title: '内容转译',
    subtitle: '从卖点到传播资产',
    text: '把品牌定位、产品卖点、电商素材、媒体投放和直播内容整理成可复用的内容表达。',
  },
  {
    step: '04',
    title: '渠道动销',
    subtitle: '线上线下承接',
    text: '用零售陈列、展会、训练营、运动场景和红包机制说明项目如何从展示走向转化。',
  },
]

const yikougegeImages = [
  { src: yikougegeProductFamily, title: '产品家族', text: '把品牌下的产品组合先整理成清晰的项目入口。' },
  { src: yikougegePackagingSystem, title: '包装系统', text: '用包装和视觉资产承接品牌识别与货架表达。' },
  { src: yikougegeContentMatrix, title: '内容矩阵', text: '把卖点、内容主题和传播素材组织成可复用资产。' },
  { src: yikougegeRetailDisplay, title: '零售陈列', text: '把线下可见性作为动销承接的一部分，而不是单独展示图。' },
  { src: yikougegeLiveCommerce, title: '直播电商', text: '将产品表达转译到电商和直播货架语境。' },
  { src: yikougegeTradeShow, title: '展会触达', text: '用展会场景补足品牌曝光和渠道沟通证据。' },
]

const kefumeiStages = [
  {
    step: '01',
    title: '信任背书',
    subtitle: '先讲为什么可信',
    text: '从品牌产品线、医疗渠道、设备/技术资料和临床案例建立“专业修护”的理解基础。',
  },
  {
    step: '02',
    title: '产品培训',
    subtitle: '把复杂功效讲成可复述脚本',
    text: '将敷料、喷雾、修复乳等产品拆成适用人群、使用时机、推荐话术和注意事项。',
  },
  {
    step: '03',
    title: '场景推荐',
    subtitle: '从成分走向使用场景',
    text: '围绕敏感、痘痘、医美术后、干痒泛红等问题，把产品能力转译为具体使用场景。',
  },
  {
    step: '04',
    title: '渠道承接',
    subtitle: '内容、门店、O2O 同步',
    text: '用达人内容、明星素材、药店陈列、O2O 头图和 IP 活动形成从认知到购买的承接链路。',
  },
]

const kefumeiImages = [
  { src: kefumeiBrandLineup, title: '品牌产品线', text: '用产品线建立项目第一层认知，而不是直接进入碎片素材。' },
  { src: kefumeiThreeProductSystem, title: '三产品系统', text: '将产品组合拆成深度修护、即时舒缓和日常保湿。' },
  { src: kefumeiMedicalChannelMap, title: '医疗渠道', text: '把渠道背书作为专业修护项目的信任入口。' },
  { src: kefumeiKolEducationMatrix, title: '达人教育', text: '用内容矩阵降低高专业产品的理解成本。' },
  { src: kefumeiRetailDisplay, title: '药店陈列', text: '门店陈列负责提高被看见和被问起的机会。' },
  { src: kefumeiO2oChannel, title: 'O2O 承接', text: '线上头图和渠道页面补齐购买决策信息。' },
]

function App() {
  useEffect(() => {
    document.title = '何坚松 Nelson | Personal Archive'
  }, [])

  const currentPath = window.location.pathname.replace(/\/$/, '')

  if (currentPath.endsWith('/projects/001')) {
    return (
      <main className="min-h-screen overflow-x-clip bg-[#0C0C0C] text-[#F4F1EA]">
        <DetailTopBar tone="dark" backHref="/me/#projects" backLabel="返回项目列表" />
        <Project001Section />
      </main>
    )
  }

  if (currentPath.endsWith('/projects/yikougege')) {
    return (
      <main className="min-h-screen overflow-x-clip bg-[#F4F1EA] text-[#111]">
        <DetailTopBar backHref="/me/#projects" backLabel="返回项目列表" />
        <YikougegeDetail />
      </main>
    )
  }

  if (currentPath.endsWith('/projects/kefumei')) {
    return (
      <main className="min-h-screen overflow-x-clip bg-[#F4F1EA] text-[#111]">
        <DetailTopBar backHref="/me/#projects" backLabel="返回项目列表" />
        <KefumeiDetail />
      </main>
    )
  }

  if (currentPath.endsWith('/capabilities/product')) {
    return (
      <main className="min-h-screen overflow-x-clip bg-[#F4F1EA] text-[#111]">
        <DetailTopBar backHref="/me/#capabilities" backLabel="返回能力板块" />
        <CapabilityDetail detail={capabilityDetails.product} />
      </main>
    )
  }

  if (currentPath.endsWith('/capabilities/gtm')) {
    return (
      <main className="min-h-screen overflow-x-clip bg-[#F4F1EA] text-[#111]">
        <DetailTopBar backHref="/me/#capabilities" backLabel="返回能力板块" />
        <CapabilityDetail detail={capabilityDetails.gtm} />
      </main>
    )
  }

  if (currentPath.endsWith('/capabilities/merchandise')) {
    return (
      <main className="min-h-screen overflow-x-clip bg-[#F4F1EA] text-[#111]">
        <DetailTopBar backHref="/me/#capabilities" backLabel="返回能力板块" />
        <CapabilityDetail detail={capabilityDetails.merchandise} />
      </main>
    )
  }

  if (currentPath.endsWith('/insights/radar')) {
    return (
      <main className="min-h-screen overflow-x-clip bg-[#F4F1EA] text-[#111]">
        <DetailTopBar backHref="/me/#capabilities" backLabel="返回能力板块" />
        <CapabilityDetail detail={insightPages.radar} />
      </main>
    )
  }

  if (currentPath.endsWith('/insights/methodology')) {
    return (
      <main className="min-h-screen overflow-x-clip bg-[#F4F1EA] text-[#111]">
        <DetailTopBar backHref="/me/#capabilities" backLabel="返回能力板块" />
        <CapabilityDetail detail={insightPages.methodology} />
      </main>
    )
  }

  return (
    <main className="home-page min-h-screen overflow-x-clip bg-[#0C0C0C] text-[#F4F1EA]">
      <HeroSection />
      <AboutSection />
      <TimelineSection />
      <CapabilitiesSection />
      <ProjectsSection />
      <ContactSection />
      {false && (
        <>
      <Project001Section />
      <ProjectDetailSection
        id="project-yikougege"
        eyebrow="Brand Project"
        title="益口葛葛项目拆解"
        intro="这个项目重点展示如何把品牌资料、产品组合、内容矩阵和渠道动销素材，整理成一套可阅读、可汇报、可继续补证据的项目案例。"
        stages={yikougegeStages}
        images={yikougegeImages}
        highlights={[
          ['项目定位', '品牌项目资料重组与展示'],
          ['核心动作', '产品家族、包装、内容、渠道、动销五层拆解'],
          ['沉淀结果', '可用于项目介绍、作品集和后续复盘的结构化素材'],
        ]}
      />
      <ProjectDetailSection
        id="project-kefumei"
        eyebrow="Product Training"
        title="可复美项目拆解"
        intro="这个项目重点展示如何把医学修护类产品资料，从技术背书、产品培训、场景推荐到渠道承接，整理成一套可被一线复述的产品内容体系。"
        stages={kefumeiStages}
        images={kefumeiImages}
        highlights={[
          ['项目定位', '产品培训与医学修护内容重组'],
          ['核心动作', '信任背书、产品系统、使用场景、渠道承接四层拆解'],
          ['沉淀结果', '可服务门店培训、O2O 页面、达人内容和项目展示的资料体系'],
        ]}
      />
        </>
      )}
    </main>
  )
}

function DetailTopBar({
  tone = 'light',
  backHref = '/me/',
  backLabel = '返回首页',
}: {
  tone?: 'light' | 'dark'
  backHref?: string
  backLabel?: string
}) {
  const isDark = tone === 'dark'

  return (
    <header className={`${isDark ? 'bg-[#0C0C0C] text-white' : 'bg-[#F4F1EA] text-[#111]'} px-5 pt-6 sm:px-8 md:px-10`}>
      <div className="mx-auto flex max-w-7xl items-center justify-between border-b border-current/10 pb-5">
        <a className="text-sm font-semibold transition hover:text-[#FF2442]" href={backHref}>
          ← {backLabel}
        </a>
        <span className="text-xs font-semibold uppercase tracking-[0.22em] opacity-45">Project Detail</span>
      </div>
    </header>
  )
}

function YikougegeDetail() {
  return (
    <ProjectDetailSection
      id="project-yikougege"
      eyebrow="Brand Project"
      title="益口葛葛项目拆解"
      intro="这个项目重点展示如何把品牌资料、产品组合、内容矩阵和渠道动销素材，整理成一套可阅读、可汇报、可继续补证据的项目案例。"
      stages={yikougegeStages}
      images={yikougegeImages}
      highlights={[
        ['项目定位', '品牌项目资料重组与展示'],
        ['核心动作', '产品家族、包装、内容、渠道、动销五层拆解'],
        ['沉淀结果', '可用于项目介绍、作品集和后续复盘的结构化素材'],
      ]}
      reasoning={[
        ['问题解决', '解决项目素材分散、表达重点不清、难以对外说明业务价值的问题。'],
        ['核心判断', '先建立产品家族和渠道场景，再判断哪些素材能服务展示、销售和复盘。'],
        ['拆解方式', '按产品组合、包装系统、内容矩阵、零售陈列、直播电商和展会触达拆开。'],
        ['业务支持', '支持项目介绍、渠道沟通、内容复用和后续资料补齐。'],
        ['复制能力', '可迁移到其他品牌项目的资料重组、渠道动销和作品集表达。'],
      ]}
    />
  )
}

function KefumeiDetail() {
  return (
    <ProjectDetailSection
      id="project-kefumei"
      eyebrow="Product Training"
      title="可复美项目拆解"
      intro="这个项目重点展示如何把医学修护类产品资料，从技术背书、产品培训、场景推荐到渠道承接，整理成一套可被一线复述的产品内容体系。"
      stages={kefumeiStages}
      images={kefumeiImages}
      highlights={[
        ['项目定位', '产品培训与医学修护内容重组'],
        ['核心动作', '信任背书、产品系统、使用场景、渠道承接四层拆解'],
        ['沉淀结果', '可服务门店培训、O2O 页面、达人内容和项目展示的资料体系'],
      ]}
      reasoning={[
        ['问题解决', '解决医学修护类资料专业度高、内容碎片化、一线难复述的问题。'],
        ['核心判断', '先建立信任背书，再把功效转译成使用场景和渠道话术。'],
        ['拆解方式', '按产品线、三产品系统、医疗渠道、达人教育、药店陈列和 O2O 承接拆开。'],
        ['业务支持', '支持门店培训、达人内容、O2O 页面、药店陈列和项目展示。'],
        ['复制能力', '可迁移到高专业度个护、医美修护和功能性产品的内容培训体系。'],
      ]}
    />
  )
}

function FadeIn({
  children,
  className,
  delay = 0,
  y = 28,
}: {
  children: ReactNode
  className?: string
  delay?: number
  y?: number
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ duration: 0.65, delay, ease }}
    >
      {children}
    </motion.div>
  )
}

function HeroSection() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <section className="home-hero relative isolate flex min-h-screen flex-col overflow-hidden border-b border-white/[0.08]">
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(115deg,#0C0C0C_0%,#15120F_48%,#0C0C0C_100%)]" />
      <div className="absolute inset-x-0 top-0 -z-10 h-px bg-gradient-to-r from-transparent via-white/35 to-transparent" />

      <FadeIn y={-16}>
        <nav className="home-nav mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 text-xs uppercase tracking-[0.26em] text-white/72 sm:px-8 md:px-10">
          <a href="/me/" className="home-brand font-semibold text-white">
            <span>Nelson</span>
            <span>Archive</span>
          </a>
          <div className="hidden items-center gap-8 sm:flex">
            {navItems.map((item) => (
              <a key={item.href} href={item.href} className="transition hover:text-white">
                {item.label}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <a href="/me/logout" className="hidden items-center gap-2 rounded-full border border-white/15 px-3 py-2 text-[0.68rem] text-white/70 transition hover:border-white/30 hover:text-white sm:inline-flex">
              <LockKeyhole className="h-3.5 w-3.5" />
              退出
            </a>
            <button type="button" aria-label={mobileMenuOpen ? '关闭导航菜单' : '打开导航菜单'} aria-expanded={mobileMenuOpen} aria-controls="mobile-navigation" onClick={() => setMobileMenuOpen((open) => !open)} className="home-menu inline-flex h-[54px] w-[54px] items-center justify-center rounded-full border border-white/25 text-white transition hover:border-white/60 sm:hidden">
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </nav>
      </FadeIn>

      <AnimatePresence>
        {mobileMenuOpen ? <motion.div id="mobile-navigation" initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.2, ease }} className="absolute inset-x-5 top-[88px] z-20 rounded-[18px] border border-white/10 bg-[#151515]/95 p-3 shadow-2xl shadow-black/35 backdrop-blur-xl sm:hidden">
          {navItems.map((item) => <a key={item.href} href={item.href} onClick={() => setMobileMenuOpen(false)} className="flex min-h-[48px] items-center justify-between rounded-xl px-4 text-sm font-semibold text-white/82 transition hover:bg-white/10 hover:text-white">{item.label}<ArrowUpRight className="h-4 w-4 text-[#FF2442]" /></a>)}
          <a href="/me/logout" className="mt-2 flex min-h-[48px] items-center gap-3 rounded-xl border border-white/10 px-4 text-sm font-semibold text-white/82"><LockKeyhole className="h-4 w-4 text-[#FF2442]" />退出</a>
        </motion.div> : null}
      </AnimatePresence>

      <div className="home-hero-grid mx-auto grid w-full max-w-7xl flex-1 items-center gap-12 px-5 pb-12 pt-10 sm:px-8 md:grid-cols-[minmax(0,0.95fr)_minmax(360px,0.78fr)] md:px-10 md:pb-16">
        <div className="home-hero-copy">
          <FadeIn>
            <p className="mb-6 inline-flex rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs uppercase tracking-[0.28em] text-white/64">
              Private Personal Archive
            </p>
          </FadeIn>
          <FadeIn delay={0.08}>
            <h1 className="nelson-heading text-[clamp(4.6rem,13vw,12rem)] font-black uppercase leading-[0.82] tracking-[-0.04em]">
              Nelson
            </h1>
            <h2 className="mt-5 text-[clamp(2.4rem,6vw,5.8rem)] font-semibold leading-none tracking-[-0.04em] text-white">
              何坚松
            </h2>
          </FadeIn>
          <FadeIn delay={0.16}>
            <p className="mt-8 max-w-2xl text-lg leading-8 text-white/70 md:text-xl md:leading-9">
              一个从市场一线走向产品中心的人，正在把市场经验、项目执行、内容表达和 AI 工作流整合成自己的长期能力。
            </p>
          </FadeIn>
          <FadeIn delay={0.24}>
            <div className="home-hero-actions mt-9 flex flex-wrap gap-3">
              <a className="inline-flex items-center gap-2 rounded-full bg-[#FF2442] px-6 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#ff3d57]" href="#timeline">
                查看经历
                <ArrowUpRight className="h-4 w-4" />
              </a>
              <a className="inline-flex items-center gap-2 rounded-full border border-white/14 px-6 py-3 text-sm font-semibold text-white/80 transition hover:-translate-y-0.5 hover:border-white/30 hover:text-white" href="#projects">
                查看项目
              </a>
              <a className="inline-flex items-center gap-2 rounded-full border border-white/14 px-6 py-3 text-sm font-semibold text-white/80 transition hover:-translate-y-0.5 hover:border-white/30 hover:text-white" href="#contact">
                联系我
              </a>
            </div>
          </FadeIn>
        </div>

        <FadeIn delay={0.2} className="home-hero-visual relative min-h-[560px] md:min-h-[640px]">
          <HeroCharacterScene />
          <motion.div
            className="home-metrics absolute bottom-6 left-5 right-5 rounded-2xl border border-white/[0.08] bg-[#111]/85 p-4 backdrop-blur-md md:bottom-8"
            initial={{ opacity: 0, y: 18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.55, delay: 0.55, ease }}
          >
            <div className="grid grid-cols-3 gap-3 text-center">
              <Metric label="起点" value="香港" />
              <Metric label="路径" value="深圳" />
              <Metric label="现在" value="北京" />
            </div>
          </motion.div>
        </FadeIn>
      </div>
    </section>
  )
}

function HeroCharacterScene() {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100)
    camera.position.set(0, 0.1, 6.4)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setClearColor(0x000000, 0)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.domElement.className = 'h-full w-full'
    renderer.domElement.setAttribute('aria-label', 'Nelson 3D interactive character scene')
    container.appendChild(renderer.domElement)

    const group = new THREE.Group()
    scene.add(group)

    const characterGeometry = new THREE.PlaneGeometry(2.38, 5.15, 24, 24)
    const characterMaterial = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      side: THREE.DoubleSide,
    })
    const character = new THREE.Mesh(characterGeometry, characterMaterial)
    character.position.set(0.22, -0.2, 0.4)
    group.add(character)

    const characterTexture = new THREE.TextureLoader().load(nelsonHeroCharacter, (texture) => {
      texture.colorSpace = THREE.SRGBColorSpace
      texture.anisotropy = renderer.capabilities.getMaxAnisotropy()
      characterMaterial.map = texture
      characterMaterial.needsUpdate = true
    })

    const haloGeometry = new THREE.PlaneGeometry(4.2, 5.5)
    const haloMaterial = new THREE.MeshBasicMaterial({
      color: 0x171717,
      transparent: true,
      opacity: 0.64,
      side: THREE.DoubleSide,
    })
    const halo = new THREE.Mesh(haloGeometry, haloMaterial)
    halo.position.set(0.15, -0.1, -0.18)
    halo.rotation.y = -0.08
    group.add(halo)

    const panelMaterial = new THREE.MeshBasicMaterial({
      color: 0x252525,
      transparent: true,
      opacity: 0.28,
      side: THREE.DoubleSide,
    })
    const accentMaterial = new THREE.MeshBasicMaterial({
      color: 0xff2442,
      transparent: true,
      opacity: 0.44,
      side: THREE.DoubleSide,
    })

    const panels: THREE.Mesh[] = []
    for (let index = 0; index < 8; index += 1) {
      const panel = new THREE.Mesh(new THREE.PlaneGeometry(0.58 + index * 0.06, 1.05 + index * 0.04), index === 5 ? accentMaterial : panelMaterial)
      panel.position.set(index % 2 === 0 ? -1.95 - index * 0.03 : 1.7 + index * 0.04, 1.8 - index * 0.52, -0.7 - index * 0.08)
      panel.rotation.y = index % 2 === 0 ? 0.32 : -0.42
      panel.rotation.z = index % 3 === 0 ? 0.05 : -0.035
      panels.push(panel)
      group.add(panel)
    }

    const pointer = new THREE.Vector2(0, 0)
    const targetPointer = new THREE.Vector2(0, 0)

    const handlePointerMove = (event: PointerEvent) => {
      const rect = container.getBoundingClientRect()
      targetPointer.x = ((event.clientX - rect.left) / rect.width - 0.5) * 2
      targetPointer.y = -(((event.clientY - rect.top) / rect.height - 0.5) * 2)
    }

    const handlePointerLeave = () => targetPointer.set(0, 0)

    container.addEventListener('pointermove', handlePointerMove)
    container.addEventListener('pointerleave', handlePointerLeave)

    const resize = () => {
      const width = container.clientWidth
      const height = container.clientHeight
      renderer.setSize(width, height, false)
      camera.aspect = width / Math.max(height, 1)
      camera.updateProjectionMatrix()
    }

    const resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(container)
    resize()

    let frameId = 0
    const clock = new THREE.Clock()

    const animate = () => {
      const elapsed = clock.getElapsedTime()
      pointer.lerp(targetPointer, 0.065)

      group.rotation.y = pointer.x * 0.12
      group.rotation.x = pointer.y * 0.045
      character.rotation.y = pointer.x * 0.08
      character.rotation.x = pointer.y * 0.035
      character.position.y = -0.2 + Math.sin(elapsed * 0.8) * 0.035
      halo.position.y = -0.1 + Math.sin(elapsed * 0.65) * 0.02

      panels.forEach((panel, index) => {
        panel.position.y += Math.sin(elapsed * 0.8 + index) * 0.0009
      })

      camera.position.x += (pointer.x * 0.16 - camera.position.x) * 0.04
      camera.position.y += (0.1 + pointer.y * 0.12 - camera.position.y) * 0.04
      camera.lookAt(0, 0, 0)

      renderer.render(scene, camera)
      frameId = window.requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.cancelAnimationFrame(frameId)
      resizeObserver.disconnect()
      container.removeEventListener('pointermove', handlePointerMove)
      container.removeEventListener('pointerleave', handlePointerLeave)
      renderer.domElement.remove()
      characterTexture.dispose()
      characterGeometry.dispose()
      characterMaterial.dispose()
      haloGeometry.dispose()
      haloMaterial.dispose()
      panelMaterial.dispose()
      accentMaterial.dispose()
      panels.forEach((panel) => panel.geometry.dispose())
      renderer.dispose()
    }
  }, [])

  return (
    <div className="relative h-[560px] overflow-visible md:h-[640px]">
      <div ref={containerRef} className="absolute inset-0" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_58%_38%,rgba(255,255,255,0.08),transparent_28%),linear-gradient(180deg,transparent_62%,rgba(12,12,12,0.5)_100%)]" />
      <div className="pointer-events-none absolute left-5 top-5 rounded-full border border-white/[0.08] bg-white/[0.04] px-3 py-1 text-[0.64rem] uppercase tracking-[0.24em] text-white/50">
        Interactive 3D
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[0.68rem] uppercase tracking-[0.24em] text-white/42">{label}</div>
      <div className="mt-1 text-lg font-semibold text-white">{value}</div>
    </div>
  )
}

function AboutSection() {
  const blocks = [
    {
      eyebrow: '我是谁',
      title: '何坚松，Nelson。',
      body: '我的职业路径不是一开始就固定在某个岗位上，而是从真实业务现场里一步步长出来的。',
    },
    {
      eyebrow: '我从哪里来',
      title: '从市场一线开始。',
      body: '香港阶段让我先接触用户、渠道和销售场景，也让我开始理解表达和信任对项目结果的影响。',
    },
    {
      eyebrow: '我现在关注什么',
      title: '靠近产品中心。',
      body: '现在我更关注用户、需求、内容、产品和结果之间的完整链路，以及过程中的资料沉淀。',
    },
  ]

  return (
    <section id="about" className="home-about bg-[#F4F1EA] px-5 py-20 text-[#111] sm:px-8 md:px-10 md:py-28">
      <div className="mx-auto max-w-7xl">
        <FadeIn>
          <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[#FF2442]">About Nelson</p>
          <h2 className="max-w-4xl text-[clamp(2.7rem,7vw,6.8rem)] font-black leading-[0.9] tracking-[-0.05em]">
            从市场一线，到产品中心。
          </h2>
        </FadeIn>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {blocks.map((block, index) => (
            <FadeIn key={block.title} delay={index * 0.08}>
              <article className="min-h-[260px] rounded-[28px] border border-black/10 bg-white p-7 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-black/10">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-black/42">{block.eyebrow}</p>
                <h3 className="mt-7 text-3xl font-semibold tracking-[-0.04em]">{block.title}</h3>
                <p className="mt-5 text-base leading-8 text-black/62">{block.body}</p>
              </article>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}

function TimelineSection() {
  return (
    <section id="timeline" className="home-timeline bg-[#0C0C0C] px-5 py-20 text-white sm:px-8 md:px-10 md:py-28">
      <div className="mx-auto max-w-7xl">
        <FadeIn>
          <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
            <div>
              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[#FF2442]">Timeline</p>
              <h2 className="text-[clamp(2.8rem,7vw,7rem)] font-black leading-[0.9] tracking-[-0.05em]">经历时间线</h2>
            </div>
            <p className="max-w-lg text-base leading-8 text-white/58">
              三个阶段先保持清晰，后面可以继续补公司、岗位和代表事件。
            </p>
          </div>
        </FadeIn>

        <div className="mt-12 border-t border-white/10">
          {timelineItems.map((item, index) => (
            <FadeIn key={item.id} delay={index * 0.08}>
              <article className="grid gap-6 border-b border-white/10 py-9 md:grid-cols-[0.2fr_0.32fr_0.48fr] md:items-start md:py-12">
                <div><p className="text-sm font-semibold text-[#FF2442]">0{index + 1}</p><p className="mt-3 text-sm text-white/45">{item.period}</p></div>
                <div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/42">{item.city}</p><h3 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">{item.title}</h3></div>
                <div><p className="text-base leading-8 text-white/66">{item.summary}</p><div className="mt-5 flex flex-wrap gap-x-4 gap-y-2 text-sm text-white/45">{item.tags.map((tag) => <span key={tag}>/{tag}</span>)}</div></div>
              </article>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}

function InfoPill({ icon, text }: { icon: ReactNode; text: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white/68">
      {icon}
      {text}
    </span>
  )
}

function CapabilitiesSection() {
  return (
    <section id="capabilities" className="home-capabilities bg-[#0C0C0C] px-5 py-20 text-white sm:px-8 md:px-10 md:py-28">
      <div className="mx-auto max-w-7xl">
        <FadeIn>
          <div className="grid gap-6 border-b border-white/10 pb-10 md:grid-cols-[0.82fr_1.18fr] md:items-end">
            <div>
              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[#FF2442]">Capability Map</p>
              <h2 className="text-[clamp(2.8rem,7vw,7rem)] font-black leading-[0.9] tracking-[-0.05em]">能力板块</h2>
            </div>
            <p className="max-w-2xl text-base leading-8 text-white/58">
              首页只放入口，不堆证明材料。详细的判断过程、方法论和数据库能力进入独立页面展开。
            </p>
          </div>
        </FadeIn>

        <div className="mt-12 border-t border-[color:var(--border-on-dark)]">
          {capabilitySections.map((section, index) => (
            <FadeIn key={section.id} delay={index * 0.08}>
              <motion.a
                href={section.href}
                className="group grid gap-6 border-b border-[color:var(--border-on-dark)] py-8 transition md:grid-cols-[0.15fr_0.28fr_0.47fr_0.1fr] md:items-center md:py-11"
                whileHover={{ x: 6 }}
              >
                <span className="text-4xl font-black tracking-[-0.08em] text-[var(--accent)]">{section.index}</span>
                <div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/42">{section.eyebrow}</p><h3 className="mt-3 text-3xl font-black tracking-[-0.05em]">{section.title}</h3></div>
                <div><p className="text-base leading-8 text-[color:var(--text-on-dark-muted)]">{section.summary}</p><p className="mt-4 text-sm text-white/44">{section.tags.join(' / ')}</p></div>
                <ArrowUpRight className="h-6 w-6 text-white/35 transition group-hover:text-[var(--accent)]" />
              </motion.a>
            </FadeIn>
          ))}
        </div>

        <FadeIn>
          <div className="mt-5 flex flex-wrap gap-3">
            <a className="inline-flex items-center gap-2 rounded-full border border-white/12 px-5 py-3 text-sm font-semibold text-white/72 transition hover:border-white/28 hover:text-white" href="/me/insights/radar">
              查看行业雷达
              <ArrowUpRight className="h-4 w-4" />
            </a>
            <a className="inline-flex items-center gap-2 rounded-full border border-white/12 px-5 py-3 text-sm font-semibold text-white/72 transition hover:border-white/28 hover:text-white" href="/me/insights/methodology">
              查看方法论资产
              <ArrowUpRight className="h-4 w-4" />
            </a>
          </div>
        </FadeIn>
      </div>
    </section>
  )
}

function ProjectsSection() {
  const active = projects[0]

  return (
    <section id="projects" className="home-projects bg-[#F4F1EA] px-5 py-20 text-[#111] sm:px-8 md:px-10 md:py-28">
      <div className="mx-auto max-w-7xl">
        <FadeIn>
          <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
            <div>
              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[#FF2442]">Project Archive</p>
              <h2 className="text-[clamp(2.8rem,7vw,7rem)] font-black leading-[0.9] tracking-[-0.05em]">项目作品</h2>
            </div>
            <p className="max-w-xl text-base leading-8 text-black/58">
              首页只保留高效的项目入口和判断信息，详细流程、图片和复盘内容进入项目明细页查看。
            </p>
          </div>
        </FadeIn>

        <div className="mt-12 grid gap-10 lg:grid-cols-[1.35fr_0.65fr] lg:items-end">
          <motion.article className="overflow-hidden rounded-[26px] bg-[#111] text-white" initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5, ease }}>
            <img className="aspect-[16/10] w-full object-cover opacity-85" src={active.cover} alt={active.name} loading="lazy" decoding="async" />
            <div className="grid gap-7 p-7 md:grid-cols-[auto_1fr] md:p-10">
              <span className="text-6xl font-black tracking-[-0.08em] text-[#FF2442]">{active.index}</span>
              <div>
                <p className="text-sm font-semibold tracking-[0.08em] text-white/55">{active.type}</p>
                <h3 className="mt-3 text-[clamp(2rem,4vw,4.5rem)] font-black leading-[0.95] tracking-[-0.06em]">{active.name}</h3>
                <p className="mt-5 max-w-2xl text-base leading-8 text-white/68">{active.description}</p>
                <a className="mt-7 inline-flex items-center gap-2 border-b border-[#FF2442] pb-2 text-sm font-semibold text-white transition hover:text-[#FF2442]" href={active.detailUrl}>查看完整案例<ArrowUpRight className="h-4 w-4" /></a>
              </div>
            </div>
          </motion.article>

          <div className="border-t border-black/15">
            <p className="py-5 text-xs font-semibold uppercase tracking-[0.22em] text-black/42">Selected work</p>
            {projects.map((project) => (
              <a key={project.id} href={project.detailUrl} className="group grid grid-cols-[auto_1fr_auto] items-center gap-4 border-t border-black/10 py-6 transition hover:pl-2">
                <span className="text-xl font-black tracking-[-0.07em] text-[#FF2442]">{project.index}</span>
                <div><h3 className="text-xl font-semibold tracking-[-0.04em]">{project.name}</h3><p className="mt-2 text-sm text-black/52">{project.type}</p></div>
                <ArrowUpRight className="h-5 w-5 text-black/35 transition group-hover:text-[#FF2442]" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function ContactSection() {
  const contacts = [
    {
      label: '邮箱',
      value: 'kinsongho@qq.com',
      href: 'mailto:kinsongho@qq.com',
    },
    {
      label: '备用邮箱',
      value: 'sososong28@gmail.com',
      href: 'mailto:sososong28@gmail.com',
    },
    {
      label: '电话',
      value: '15626470290',
      href: 'tel:15626470290',
    },
  ]

  return (
    <section id="contact" className="home-contact bg-[#0C0C0C] px-5 py-20 text-white sm:px-8 md:px-10 md:py-28">
      <div className="mx-auto max-w-7xl">
        <FadeIn>
          <div className="grid gap-8 border-b border-white/10 pb-10 md:grid-cols-[0.82fr_1.18fr] md:items-end">
            <div>
              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[#FF2442]">Contact</p>
              <h2 className="text-[clamp(2.8rem,7vw,7rem)] font-black leading-[0.9] tracking-[-0.05em]">联系方式</h2>
            </div>
            <p className="max-w-2xl text-base leading-8 text-white/58">
              适合项目合作、产品岗位沟通、业务交流或进一步查看完整案例。
            </p>
          </div>
        </FadeIn>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {contacts.map((item, index) => (
            <FadeIn key={item.value} delay={index * 0.08}>
              <motion.a
                href={item.href}
                className="group block rounded-[30px] border border-white/[0.08] bg-[#151515] p-6 transition hover:-translate-y-1 hover:border-[#FF2442]/50 hover:bg-[#181818]"
                whileHover={{ y: -4 }}
              >
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/42">{item.label}</p>
                <div className="mt-8 flex items-end justify-between gap-4">
                  <span className="break-all text-2xl font-semibold tracking-[-0.03em] text-white md:text-3xl">{item.value}</span>
                  <ArrowUpRight className="h-5 w-5 shrink-0 text-[#FF2442]" />
                </div>
              </motion.a>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}

function Project001Section() {
  return (
    <section id="project-001" className="bg-[#0C0C0C] px-5 py-20 text-white sm:px-8 md:px-10 md:py-28">
      <div className="mx-auto max-w-7xl">
        <FadeIn>
          <div className="grid gap-8 border-b border-white/10 pb-12 md:grid-cols-[0.86fr_1.14fr] md:items-end">
            <div>
              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[#FF2442]">Featured Project</p>
              <h2 className="text-[clamp(2.7rem,7vw,6.8rem)] font-black leading-[0.9] tracking-[-0.05em]">
                001 产品开发与 AI 营销创新
              </h2>
            </div>
            <p className="text-lg leading-9 text-white/66">
              基于消费者洞察白皮书、145 人消费者问卷、53 人命名调研、产品屋和卖点决策汇报，按完整开发流程整理为：调研、验证、立项、实现和营销计划。
            </p>
          </div>
        </FadeIn>

        <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {evidenceCards.map((card, index) => (
            <FadeIn key={card.label} delay={index * 0.07}>
              <article className="rounded-[22px] border border-white/10 bg-white/[0.055] p-5">
                <div className="text-4xl font-black tracking-[-0.08em] text-[#FF2442]">{card.value}</div>
                <h3 className="mt-4 text-xl font-semibold">{card.label}</h3>
                <p className="mt-2 text-sm leading-6 text-white/55">{card.note}</p>
              </article>
            </FadeIn>
          ))}
        </div>

        <ProjectReasoningBlock
          tone="dark"
          items={[
            ['问题解决', '解决 001 产品容易陷入“更薄、更刺激、更多成分”的参数竞争问题，重新回到真实体验里的中断点。'],
            ['核心判断', '用户并不只是在买薄感，而是在买过程稳定、低打扰、舒服和安心。'],
            ['拆解方式', '用调研、问卷、命名测试、产品屋、RTB 和 AI 营销验证拆成完整开发链路。'],
            ['业务支持', '支持研发测试、包装表达、详情页内容、渠道讲解和营销互动入口同步。'],
            ['复制能力', '这套方法可迁移到健康个护、新消费和高私密度产品的概念验证。'],
          ]}
        />

        <div className="mt-14 grid gap-4 md:grid-cols-5">
          {developmentStages.map((stage, index) => (
            <FadeIn key={stage.step} delay={index * 0.06}>
              <article className="min-h-[270px] rounded-[26px] border border-white/10 bg-[#151515] p-5">
                <div className="text-3xl font-black tracking-[-0.08em] text-[#FF2442]">{stage.step}</div>
                <p className="mt-6 text-xs font-semibold uppercase tracking-[0.2em] text-white/40">{stage.subtitle}</p>
                <h3 className="mt-3 text-2xl font-semibold">{stage.title}</h3>
                <p className="mt-4 text-sm leading-7 text-white/62">{stage.text}</p>
              </article>
            </FadeIn>
          ))}
        </div>

        <div className="mt-14 grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
          <FadeIn>
            <section className="h-full rounded-[34px] border border-white/10 bg-[#151515] p-7 md:p-8">
              <div className="flex items-center gap-3 text-[#FF2442]">
                <PackageCheck className="h-5 w-5" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Product House</span>
              </div>
              <h3 className="mt-8 text-4xl font-black leading-tight tracking-[-0.04em]">底层需求 → 中层价值 → 顶层表达</h3>
              <p className="mt-6 text-base leading-8 text-white/64">
                001 的机会不是只做“更薄 / 更刺激 / 更多成分”，而是基于用户语言把“略干、偏干、中后期容易涩、拉扯感、会不会破”转译为产品目标。
              </p>
              <div className="mt-8 grid gap-3">
                <ValueLine label="POP" value="保留 001 品类基础心智：薄感、贴近、低异物感" />
                <ValueLine label="POD" value="水性聚氨酯 001 贴肤基底 + 重组玻尿酸双层稳态润滑" />
                <ValueLine label="RTB" value="亲水性、铺展均匀、水润留存、摩擦稳定、安心支撑" />
              </div>
            </section>
          </FadeIn>

          <FadeIn delay={0.08}>
            <figure className="overflow-hidden rounded-[34px] border border-white/10 bg-white">
              <img className="aspect-[4/3] h-full w-full object-cover object-left-top" src={jikex001ProductHouse} alt="001 产品屋" loading="lazy" decoding="async" />
            </figure>
          </FadeIn>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <FadeIn>
            <section className="rounded-[34px] border border-white/10 bg-[#F4F1EA] p-7 text-[#111] md:p-8">
              <div className="flex items-center gap-3 text-[#FF2442]">
                <BrainCircuit className="h-5 w-5" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">AI Marketing</span>
              </div>
              <h3 className="mt-8 text-4xl font-black leading-tight tracking-[-0.04em]">AI 营销创新验证</h3>
              <p className="mt-6 text-base leading-8 text-black/64">
                私密产品不适合高打扰、强推销、尴尬式教育。AI 在这里的作用是连接场景、情绪、沟通和卖点，先验证更轻、更私密的互动入口。
              </p>
              <ul className="mt-7 grid gap-3">
                {aiMarketing.map((item) => (
                  <li key={item} className="flex gap-3 text-sm leading-7 text-black/68">
                    <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-[#FF2442]" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </section>
          </FadeIn>

          <FadeIn delay={0.08}>
            <section className="h-full rounded-[34px] border border-white/10 bg-white/[0.055] p-7 md:p-8">
              <div className="flex items-center gap-3 text-[#FF2442]">
                <Sparkles className="h-5 w-5" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Implementation</span>
              </div>
              <h3 className="mt-8 text-4xl font-black leading-tight tracking-[-0.04em]">实现计划</h3>
              <div className="mt-7 grid gap-3">
                <ValueLine label="产品" value="薄感贴近 + 玻尿酸顺滑，解决距离感与摩擦感" />
                <ValueLine label="包装" value="同时承接薄感、水润、双层稳态和高端 001 升级" />
                <ValueLine label="详情页" value="第一屏讲清主卖点，机制页解释铺展、补水和减摩" />
                <ValueLine label="测试" value="渗透压、摩擦系数、保水/失水率、相容性、刺激性" />
              </div>
            </section>
          </FadeIn>
        </div>

        <div className="mt-14 grid gap-5 lg:grid-cols-3">
          {projectImages.map((image, index) => (
            <FadeIn key={image.title} delay={index * 0.08}>
              <article className="overflow-hidden rounded-[28px] border border-white/10 bg-[#151515]">
                <img className="aspect-[4/3] w-full object-cover object-left-top" src={image.src} alt={image.title} loading="lazy" decoding="async" />
                <div className="p-6">
                  <h3 className="text-2xl font-semibold">{image.title}</h3>
                  <p className="mt-4 text-sm leading-7 text-white/62">{image.text}</p>
                </div>
              </article>
            </FadeIn>
          ))}
        </div>

        <FadeIn>
          <section className="mt-5 rounded-[34px] border border-white/10 bg-white/[0.055] p-7 md:p-8">
            <div className="flex items-center gap-3 text-[#FF2442]">
              <MessageCircle className="h-5 w-5" />
              <span className="text-sm font-semibold uppercase tracking-[0.18em]">Final Expression</span>
            </div>
            <div className="mt-8 grid gap-4 md:grid-cols-3">
              <Expression label="项目命名" value="网站暂用“001 产品开发与 AI 营销创新”" />
              <Expression label="卖点表达" value="薄感贴近，玻尿酸顺滑" />
              <Expression label="命名提醒" value="潮水 / 潮涌 / 即刻需以最终业务版本为准" />
            </div>
          </section>
        </FadeIn>

        <DisclosureNotice tone="dark" />
      </div>
    </section>
  )
}

function ProjectReasoningBlock({
  items,
  tone = 'light',
}: {
  items: Array<[string, string]>
  tone?: 'light' | 'dark'
}) {
  const isDark = tone === 'dark'

  return (
    <FadeIn>
      <section className={`mt-10 rounded-[30px] border p-6 md:p-7 ${
        isDark ? 'border-white/10 bg-[#151515] text-white' : 'border-black/10 bg-white text-[#111] shadow-lg shadow-black/[0.04]'
      }`}>
        <div className="flex items-center gap-3 text-[#FF2442]">
          <Layers3 className="h-5 w-5" />
          <span className="text-sm font-semibold uppercase tracking-[0.18em]">Reasoning Chain</span>
        </div>
        <div className="mt-7 grid gap-3 md:grid-cols-5">
          {items.map(([label, value]) => (
            <article key={label} className={`rounded-2xl border p-4 ${isDark ? 'border-white/10 bg-white/[0.04]' : 'border-black/10 bg-black/[0.025]'}`}>
              <h3 className="text-sm font-black text-[#FF2442]">{label}</h3>
              <p className={`mt-3 text-sm leading-7 ${isDark ? 'text-white/62' : 'text-black/62'}`}>{value}</p>
            </article>
          ))}
        </div>
      </section>
    </FadeIn>
  )
}

function DisclosureNotice({ tone = 'light' }: { tone?: 'light' | 'dark' }) {
  const isDark = tone === 'dark'

  return (
    <FadeIn>
      <p className={`mt-8 rounded-2xl border px-5 py-4 text-sm leading-7 ${
        isDark ? 'border-white/10 bg-white/[0.04] text-white/48' : 'border-black/10 bg-black/[0.025] text-black/48'
      }`}>
        脱敏说明：页面只展示方法、结构和可公开呈现的素材，涉及未公开数据、内部价格、渠道策略和商业敏感信息均已做脱敏处理。
      </p>
    </FadeIn>
  )
}

function ProjectDetailSection({
  id,
  eyebrow,
  title,
  intro,
  stages,
  images,
  highlights,
  reasoning,
}: {
  id: string
  eyebrow: string
  title: string
  intro: string
  stages: Array<{ step: string; title: string; subtitle: string; text: string }>
  images: Array<{ src: string; title: string; text: string }>
  highlights: Array<[string, string]>
  reasoning?: Array<[string, string]>
}) {
  return (
    <section id={id} className="bg-[#F4F1EA] px-5 py-20 text-[#111] sm:px-8 md:px-10 md:py-28">
      <div className="mx-auto max-w-7xl">
        <FadeIn>
          <div className="grid gap-8 border-b border-black/10 pb-12 md:grid-cols-[0.86fr_1.14fr] md:items-end">
            <div>
              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[#FF2442]">{eyebrow}</p>
              <h2 className="text-[clamp(2.7rem,7vw,6.8rem)] font-black leading-[0.9] tracking-[-0.05em]">
                {title}
              </h2>
            </div>
            <p className="text-lg leading-9 text-black/62">{intro}</p>
          </div>
        </FadeIn>

        {reasoning ? <ProjectReasoningBlock items={reasoning} /> : null}

        <div className="mt-12 grid gap-4 md:grid-cols-4">
          {stages.map((stage, index) => (
            <FadeIn key={stage.step} delay={index * 0.06}>
              <article className="min-h-[265px] rounded-[26px] border border-black/10 bg-white p-5 shadow-lg shadow-black/[0.04]">
                <div className="text-4xl font-black tracking-[-0.08em] text-[#FF2442]">{stage.step}</div>
                <p className="mt-6 text-xs font-semibold uppercase tracking-[0.2em] text-black/38">{stage.subtitle}</p>
                <h3 className="mt-3 text-2xl font-semibold tracking-[-0.04em]">{stage.title}</h3>
                <p className="mt-4 text-sm leading-7 text-black/62">{stage.text}</p>
              </article>
            </FadeIn>
          ))}
        </div>

        <div className="mt-12 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <FadeIn>
            <section className="h-full rounded-[34px] border border-black/10 bg-[#111] p-7 text-white md:p-8">
              <div className="flex items-center gap-3 text-[#FF2442]">
                <Layers3 className="h-5 w-5" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Project Logic</span>
              </div>
              <h3 className="mt-8 text-4xl font-black leading-tight tracking-[-0.04em]">从素材堆叠到项目结构</h3>
              <p className="mt-6 text-base leading-8 text-white/64">
                这类项目最容易变成图片堆砌。拆解时先确认项目目标，再把素材按“信息来源、产品逻辑、内容表达、渠道承接、可展示结果”重新组织。
              </p>
              <div className="mt-8 grid gap-3">
                {highlights.map(([label, value]) => (
                  <ValueLine key={label} label={label} value={value} />
                ))}
              </div>
            </section>
          </FadeIn>

          <FadeIn delay={0.08}>
            <figure className="overflow-hidden rounded-[34px] border border-black/10 bg-white shadow-xl shadow-black/10">
              <img className="aspect-[4/3] h-full w-full object-cover" src={images[0].src} alt={images[0].title} loading="lazy" decoding="async" />
            </figure>
          </FadeIn>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-3">
          {images.map((image, index) => (
            <FadeIn key={image.title} delay={index * 0.05}>
              <article className="overflow-hidden rounded-[28px] border border-black/10 bg-white shadow-lg shadow-black/[0.05]">
                <img className="aspect-[4/3] w-full object-cover" src={image.src} alt={image.title} loading="lazy" decoding="async" />
                <div className="p-6">
                  <h3 className="text-2xl font-semibold tracking-[-0.04em]">{image.title}</h3>
                  <p className="mt-4 text-sm leading-7 text-black/62">{image.text}</p>
                </div>
              </article>
            </FadeIn>
          ))}
        </div>

        <DisclosureNotice />
      </div>
    </section>
  )
}

function CapabilityDetail({
  detail,
}: {
  detail: {
    eyebrow: string
    title: string
    intro: string
    thesis: string
    stages: string[][]
    examples: string[]
  }
}) {
  return (
    <section className="bg-[#F4F1EA] px-5 py-20 text-[#111] sm:px-8 md:px-10 md:py-28">
      <div className="mx-auto max-w-7xl">
        <FadeIn>
          <div className="grid gap-8 border-b border-black/10 pb-12 md:grid-cols-[0.86fr_1.14fr] md:items-end">
            <div>
              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[#FF2442]">{detail.eyebrow}</p>
              <h1 className="text-[clamp(3rem,8vw,7.2rem)] font-black leading-[0.9] tracking-[-0.05em]">{detail.title}</h1>
            </div>
            <p className="text-lg leading-9 text-black/62">{detail.intro}</p>
          </div>
        </FadeIn>

        <FadeIn>
          <section className="mt-10 rounded-[34px] border border-black/10 bg-[#111] p-7 text-white md:p-8">
            <div className="flex items-center gap-3 text-[#FF2442]">
              <Sparkles className="h-5 w-5" />
              <span className="text-sm font-semibold uppercase tracking-[0.18em]">Executive Takeaway</span>
            </div>
            <h2 className="mt-8 max-w-4xl text-4xl font-black leading-tight tracking-[-0.04em]">{detail.thesis}</h2>
          </section>
        </FadeIn>

        <div className="mt-5 grid gap-4 md:grid-cols-5">
          {detail.stages.map(([label, value], index) => (
            <FadeIn key={label} delay={index * 0.06}>
              <article className="min-h-[260px] rounded-[26px] border border-black/10 bg-white p-5 shadow-lg shadow-black/[0.04]">
                <div className="text-4xl font-black tracking-[-0.08em] text-[#FF2442]">{String(index + 1).padStart(2, '0')}</div>
                <h3 className="mt-7 text-2xl font-semibold tracking-[-0.04em]">{label}</h3>
                <p className="mt-4 text-sm leading-7 text-black/62">{value}</p>
              </article>
            </FadeIn>
          ))}
        </div>

        <FadeIn>
          <section className="mt-5 rounded-[30px] border border-black/10 bg-white p-6 shadow-lg shadow-black/[0.04] md:p-7">
            <div className="flex items-center gap-3 text-[#FF2442]">
              <FileText className="h-5 w-5" />
              <span className="text-sm font-semibold uppercase tracking-[0.18em]">Related Evidence</span>
            </div>
            <div className="mt-6 flex flex-wrap gap-3">
              {detail.examples.map((example) => (
                <span key={example} className="rounded-full border border-black/10 bg-black/[0.025] px-4 py-2 text-sm text-black/62">
                  {example}
                </span>
              ))}
            </div>
          </section>
        </FadeIn>

        <DisclosureNotice />
      </div>
    </section>
  )
}

function ValueLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
      <div className="text-xs font-black text-[#FF2442]">{label}</div>
      <div className="mt-2 text-lg font-semibold">{value}</div>
    </div>
  )
}

function Expression({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-5">
      <div className="text-xs uppercase tracking-[0.16em] text-white/42">{label}</div>
      <div className="mt-3 text-2xl font-semibold leading-tight">{value}</div>
    </div>
  )
}

function InfoLabel({ icon, text }: { icon?: ReactNode; text: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-black/[0.035] px-4 py-2 text-sm text-black/58">
      {icon}
      {text}
    </span>
  )
}

export default App
