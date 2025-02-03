import packageJson from "@/../package.json";
import Logo from "@/assets/logo/full-logo.svg?react";
import { TC_LATEST, TERMS_AND_CONDITIONS } from "@/constants/terms-and-conditions";
import { Link } from "react-router-dom";

import { Container } from "../Container/Container";
import LinkExt from "../ui/link-ext";

const Footer = () => {
  return (
    <>
      <div id="footer" className="w-full border-t-[0.8px] border-gray-600 py-[16px]">
        <Container>
          <div className="flex items-center justify-between">
            <div className="flex flex-col items-center gap-[4px]">
              <Link to="/">
                <Logo className="h-[26px]" />
              </Link>
              <p className="text-xs font-medium">Valar App v{packageJson.version}</p>
            </div>
            <div className="flex gap-4 lg:gap-9">
              <Link to="/glossary">
                <h1 className="text-sm text-gray-400">Glossary</h1>
              </Link>
              <h1 className="text-sm text-gray-400">
                <LinkExt
                  href={TERMS_AND_CONDITIONS.get(TC_LATEST)!}
                  children={"Terms of Use"}
                  className={"text-sm text-gray-400"}
                />
              </h1>
              <h1 className="text-sm text-gray-400 hidden sm:hidden md:block">
                <LinkExt
                  href={"https://valar.solutions"}
                  children={"Valar Solutions"}
                  className={"text-sm text-gray-400"}
                />
              </h1>
            </div>
          </div>
        </Container>
      </div>
    </>
  );
};

export default Footer;
