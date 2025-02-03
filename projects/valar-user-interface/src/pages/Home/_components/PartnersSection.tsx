import slide1 from "@/assets/partners/slide1.jpg";
import slide2 from "@/assets/partners/slide2.jpg";
import slide3 from "@/assets/partners/slide3.jpg";
import { Wallet } from "@/components/Wallet/Wallet";
import { Button } from "@/components/ui/button";
import {
  Carousel,
  CarouselApi,
  CarouselContent,
  CarouselDots,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const partners = [
  {
    bg: slide1,
    head: "With peer-to-peer staking you enable",
    desc: "People taking true ownership of all their assets - even plane tickets.",
  },
  {
    bg: slide2,
    head: "With peer-to-peer staking you enable",
    desc: "Unlocking capital and accessible investment options with tokenization of real estate.",
  },
  {
    bg: slide3,
    head: "With peer-to-peer staking you enable",
    desc: "Efficient, accessible, and borderless financial rails with instant settlement.",
  },
];

const PartnersSection = () => {
  const [api, setApi] = useState<CarouselApi>()
  const [current, setCurrent] = useState(0)
  const [count, setCount] = useState(0)
  const navigate = useNavigate();
  const {activeWallet} = useWallet();

  useEffect(() => {
    if (!api) {
      return
    }

    setCount(api.scrollSnapList().length)
    setCurrent(api.selectedScrollSnap())

    api.on("select", () => {
      setCurrent(api.selectedScrollSnap())
    })
  }, [api])

  return (
    <div className="flex flex-col gap-12 py-16 lg:flex-row">
      <div className="flex flex-col gap-6">
        <h1 className="text-2xl">Realize Your Blockchain Vision with Valar</h1>
        <p>
          Get started with Valar to protect your on-chain assets, give them
          opportunity to grow, and enable innovative solutions.
        </p>
        <div>
          {!activeWallet ? (
            <Wallet className="w-full lg:w-fit min-w-72" onClick={() => {navigate("stake")}} variant={"v_outline"} text={"Connect Wallet & Start Staking"}/>
          ) : (
            <Button className="w-full lg:w-fit min-w-72" variant={"v_outline"} onClick={() => navigate("stake")}>
              Start Staking
            </Button>
          )}
        </div>
      </div>
      <div className="min-h-full max-w-[800px]">
        <Carousel setApi={setApi}>
          <CarouselContent>
            {partners.map((partner, index) => (
              <CarouselItem key={index}>
                <div
                  className={`flex h-[400px] flex-col justify-end rounded-2xl`}
                  style={{
                    backgroundImage: `url(${partner.bg})`,
                    backgroundPosition: "center center",
                    backgroundSize: "cover",
                    backgroundRepeat: "no-repeat",
                  }}
                >
                  <div className="flex flex-col justify-end h-full px-4 pb-8 rounded-2xl bg-gradient-to-t from-gray-900 to-transparent">
                    <h1 className="font-bold leading-7">{partner.head}</h1>
                    <p className="leading-7">{partner.desc}</p>
                  </div>
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>
          <CarouselDots current={current} length={count}/>
          <CarouselPrevious />
          <CarouselNext />
        </Carousel>
      </div>
    </div>
  );
};

export default PartnersSection;
