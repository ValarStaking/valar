import discord from "@/assets/socials/discord.svg";
import linkedIn from "@/assets/socials/linkedin.svg";
import email from "@/assets/socials/mail.svg";
import telegram from "@/assets/socials/telegram.svg";
import { Container } from "@/components/Container/Container";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import LinkExt from "@/components/ui/link-ext";
import { Separator } from "@/components/ui/separator";
import {
  discordLink,
  emailLink,
  linkedInLink,
  telegramLink,
} from "@/constants/socials";
import { useState } from "react";

type FAQ = { ques: string; ans: JSX.Element | string };

const faqLinkStyle = "text-secondary";

function capitalizeFirstLetter(val: string): string {
  return val.charAt(0).toUpperCase() + val.slice(1);
}

const gls = (entry: string) => {
  return (
    <LinkExt
      href={"/glossary#" + entry.replace(/\s+/g, '-').toLowerCase()}
      children={entry}
      className={faqLinkStyle}/>
  );
};

const Gls = (entry: string) => {
  return (
    <LinkExt
      href={"/glossary#" + entry.replace(/\s+/g, '-').toLowerCase()}
      children={capitalizeFirstLetter(entry)}
      className={faqLinkStyle}/>
  );
};

const glspl = (entry: string) => {

  let show = entry;
  if (entry.endsWith("s")){
    show += "es";
  } else {
    show += "s";
  }

  return (
    <LinkExt
      href={"/glossary#" + entry.replace(/\s+/g, '-').toLowerCase()}
      children={entry}
      className={faqLinkStyle}/>
  );
};

const glsposs = (entry: string) => {
  return (
    <LinkExt
      href={"/glossary#" + entry.replace(/\s+/g, '-').toLowerCase()}
      children={entry + "'s"}
      className={faqLinkStyle}/>
  );
};

const StakingFAQs: FAQ[] = [
  {
    ques: "What is staking?",
    ans: (
      <span>
        {Gls("staking")} is the process of confirming transactions and producing new blocks on the blockchain {gls("network")}, thus crucially contributing to the {glsposs("network")} security.

      </span>
    ),
  },
  {
    ques: "What does it mean to stake ALGO?",
    ans: (
      <span>
        Those who stake ALGO are periodically randomly selected to confirm transactions. They do this by continuously running a computer program, which is called the {gls("Algorand daemon")}.
        The more ALGO they have, the more often they are selected, i.e., the more they contribute to {glsposs("Algorand")} security.

      </span>
    ),
  },
  {
    ques: "How to stake?",
    ans: (
      <span>
        To stake you must have access to a computer, commonly called a node, that is running a specific computer program, i.e. the {gls("Algorand daemon")}.
        This program must run uninterruptedly 24 hours a day, 7 days a week, 365 days a year.
        With Valar, you can find a node runner that will run the node on your behalf.
        Via Valar, you conclude a contract directly with the node runner for this service.

      </span>
    ),
  },
  {
    ques: "Why to stake?",
    ans: (
      <div>
        By {gls("staking")}, you are protecting your assets as well as all others on the {gls("Algorand")} network.
        You can also grow your assets thanks to {glsposs("Algorand")} {gls("staking rewards")}.
        When you stake, you empower solutions that rely on the {gls("Algorand")} network, like:
        <ul className="ml-5 list-disc">
          <li>
            Efficient, accessible, and borderless financial rails with instant settlement
            (<LinkExt href="https://quantozpay.com/" children="Quantoz" className={faqLinkStyle}/> with is EURD and {" "}
            <LinkExt href="https://hesab.com/en/" children="HesabPay" className={faqLinkStyle}/>)
          </li>
          <li>
          Unlocking capital and accessible investment options with tokenization of real-world assets for example in real estate
          (<LinkExt href="https://www.lofty.ai/" children="LoftyAI" className={faqLinkStyle}/> and  {" "}
          <LinkExt href="http://vestaequity.net/" children="Vesta Equity" className={faqLinkStyle}/>)
          and agrobusiness (<LinkExt href="https://www.agrotoken.com/en/home" children="Agrotoken" className={faqLinkStyle}/>).
          </li>
          <li>
            Verifiable provenance of goods for supply chains (<LinkExt href="https://wholechain.com/" children="Wholechain" className={faqLinkStyle}/>) and  {" "}
            of research data (<LinkExt href="https://labtrace.io/" children="Labtrace" className={faqLinkStyle}/>).
          </li>
          <li>
            People taking true ownership of all their assets - even plane tickets (<LinkExt href="https://travelx.io/" children="TravelX" className={faqLinkStyle}/>).
        </li>
        </ul>
      </div>
    ),
  },
  {
    ques: "What are staking rewards?",
    ans: (
      <span>
        The {gls("Algorand")} network rewards users who stake because they are protecting the network and ensuring its seamless functioning by running nodes.
        The {gls("staking rewards")} come from the fees paid by {gls("Algorand")} users when they make a transaction. Additionally, the Algorand Foundation is subsidizing these rewards to further incentivize nodes to join, thus increasing the security and decentralization of the network.

      </span>
    ),
  },
  {
    ques: "Can anyone receive staking rewards?",
    ans: (
      <span>
        The {gls("Algorand")} network is distributing the fees only to {glspl("account")} that stake more than 30,000 ALGO and less than 70,000,000 ALGO.
        You can still stake with a smaller or larger amount for the many benefits of staking like protecting the {gls("Algorand")} blockchain (i.e., your assets), being eligible to vote in {gls("Algorand")} governance, etc. but you will not be eligible for {gls("staking rewards")}.

      </span>
    ),
  },
  {
    ques: "Is staking the same as mining Bitcoin?",
    ans: (
      <span>
        Staking fulfills a similar role in {gls("Algorand")} and other modern blockchains as mining Bitcoin.
        The difference is that mining Bitcoin uses much, much, much more energy.
        Most modern blockchains have moved from mining to staking because it reduces energy consumption by more than 99.9 %.


      </span>
    ),
  },
  {
    ques: "What is peer-to-peer staking?",
    ans: (
      <span>
        Peer-to-peer staking is the mechanism underpinning the Valar platform.
        It is the process of finding a node runner, which can be anywhere around the globe, and having them set up their node for you to start staking.
        By confirming the node setup, you delegate your voting rights for confirmation of new transactions and blocks in the blockchain network to the node runner, while your ALGO remains unlocked in your {gls("wallet")}.
        From the point of view of the network, it does not treat you or your {gls("account")} differently from anyone who is directly staking by themselves. The network issues all the {gls("staking rewards")} that your {gls("account")} produces directly to your {gls("wallet")}.

      </span>
    ),
  },
  {
    ques: "What does setting up a node mean?",
    ans: (
      <span>
        While any {gls("account")} can stake through any node, the node needs a way of proving to the network that it is staking on behalf of an {gls("account")}, whose owner wants to stake.
        As a proof of the {glsposs("account")} owner's agreement that the node is staking on their behalf, the node generates {gls("participation keys")} that must be confirmed by the {gls("account")}.
        The {gls("participation keys")} can be used only for verifying transactions and proposing blocks.
        The process of generating the {gls("participation keys")} is also referred to as setting up the node for a user.

      </span>
    ),
  },
  {
    ques: "How is a node setup confirmed?",
    ans: (
      <span>
        An {gls("Algorand")} {gls("account")} needs to confirm the {gls("participation keys")} that a node generated before the {gls("Algorand daemon")} on the node can start using them for staking.
        This confirmation happens when the corresponding {gls("account")} issues a so-called participation key registration transaction on the {gls("Algorand")} {gls("network")}.
        This transaction includes information about the generated {gls("participation keys")}.


      </span>
    ),
  },
  {
    ques: "Are there other staking options besides peer-to-peer staking?",
    ans: (
      <span>
        Yes, there are.
        If you have the technical skills, you can always run a node and stake directly yourself.
        In such a case, you will likely have the capacity to stake for more people than just yourself, thus you can additionally become a node runner for others via Valar.
        Other options include so&#8209;called {glspl("staking pool")} and {gls("liquid staking")}.
        With these options, you transfer your ALGO to a smart contract, which can accumulate ALGO from multiple users, and the funds on the smart contract are staked on behalf of the users.
        The smart contract may receive {gls("staking rewards")}, from which it can subtract a commission and distribute the rest to the users that contributed the staked ALGO.
        In addition to staking by yourself, peer&#8209;to&#8209;peer staking is the only solution where you always keep full custody of your ALGO.

      </span>
    ),
  },
  {
    ques: "What are staking pools?",
    ans: (
      <span>
        Staking pools are another option for {gls("staking")}.
        With these, you transfer your ALGO to a smart contract, which is then staked by the stake pool operator.
        Such staking solutions can combine ALGO from multiple users and take a commission on the {gls("staking rewards")} generated by that pool of ALGO.

      </span>
    ),
  },
  {
    ques: "What is liquid staking?",
    ans: (
      <span>
        Liquid staking is another option for {gls("staking")}.
        With these, you transfer your ALGO to a smart contract, which is then staked by someone else.
        You get another token, called a liquid staking token in return.
        </span>
    ),
  },
];

const DelegatorFAQs: FAQ[] = [
  {
    ques: "How to stake with Valar?",
    ans: (
      <span>
        You simply connect with your wallet to the Valar platform and select the duration for which you want to stake.
        The platform will suggest to you several node runners based on your current ALGO stake.
        You are free to select one of these for staking or browse and select any other node runner that is offering their services on the platform.
        You conclude a contract directly with the selected node runner based on their offering and pay for their service.
        The node runner will then automatically prepare a node for you.
        This can take a few minutes.
        You then confirm the prepared setup and that's it! You are now staking!

      </span>
    ),
  },
  {
    ques: "What is the cost of staking via Valar?",
    ans: (
      <span>
        The fees for staking are defined by each node runner individually.
        Their fees consist of two parts &#8209; a setup fee (one-time cost for preparing the node for you) and an operational fee (proportional to your selected duration of staking).
        The node runner also defines the accepted payment currency, which is normally in {glspl("stablecoin")}.
        The payment is made in advance for the staking duration.

        The Valar platform does not charge you anything for {gls("staking")}.
        The platform takes a commission on the revenue made by the node runners.

      </span>
    ),
  },
  {
    ques: "Are there any other fees?",
    ans: (
      <span>
        When staking via Valar, you have to place an ALGO deposit to cover the {glsposs("Algorand")} fees for storing your staking information on the Valar Platform.
        The deposit gets returned when you stop using the Valar Platform.
        Additionally, you are required to cover the {gls("Algorand")} transaction fees for interacting with the Valar Platform and for opting into the {glsposs("network")} staking mechanism.

      </span>
    ),
  },
  {
    ques: "Which node runner should I select for staking?",
    ans: (
      <span>
        Different node runners have varying terms and it is up to you to decide which terms are most important to you.
        For example, the fees that a node runner charges can vary because of the differences in the reliability of the service offered by node runners.
        The higher your stake, the more reliable the node should be in order not to endanger the network, and consequently your stake.
        If you use Valar through an official website, you will automatically be suggested several node runners based on your ALGO stake.

      </span>
    ),
  },
  {
    ques: "Is selection of the node runner important?",
    ans: (
      <span>
        Yes, it is.
        While the node runner does not have any access to your ALGO, if the node runner is malicious, they could attack the whole {gls("Algorand")} network if they operate more than 2/3 of the total ALGO staked.
        You should select a node runner that you trust will do good and protect the network on your behalf.

      </span>
    ),
  },
  {
    ques: "How much ALGO am I staking?",
    ans: (
      <span>
        You always stake all ALGO from your account. If your ALGO balance changes, your stake amount will automatically be updated by the {gls("Algorand")} network. For example, if you move part of the ALGO from your account or whenever you receive {gls("staking rewards")}.

      </span>
    ),
  },
  {
    ques: "Can I change my ALGO stake balance?",
    ans: (
      <div>
        Yes! Your ALGO is completely unlocked and in your sole custody at all times. You can spend it or get more ALGO.
        Your stake will be automatically updated by the {gls("Algorand")} network.
        It is important to note that that
        <ul className="ml-5 list-disc">
          <li>
            If your ALGO stake falls below 30,000 ALGO, you will not qualify anymore for {gls("Algorand")} network's staking rewards.
          </li>
          <li>
            If your ALGO stake increases above the maximum agreed with your node runner, your service contract might get terminated.
          </li>
        </ul>
      </div>
    ),
  },
  {
    ques: "What is the maximum ALGO I can stake?",
    ans: (
      <span>
        Your selected node runner might define a maximum limit on the amount of ALGO you can stake with them.
        This is because your ALGO stake determines how often the node runner will be selected to produce a block on the {gls("Algorand")} network on your behalf.
        That is, the more ALGO you have staked through them, the more work they have, thus they might charge more for a larger stake.
        When you conclude the service contract with the node runner, you define the maximum stake that you will have in your account balance during the staking duration.

      </span>
    ),
  },
  {
    ques: "How to select the maximum stake?",
    ans: (
      <span>
        The maximum stake should equal at least your current stake, otherwise you will not be able to conclude a contract.
        It is recommended to select at least a 10% buffer so that you can get some additional ALGO, for example, from staking rewards.

        If you want to transfer more ALGO into your account to stake, you can withdraw from your service contract at any point in time and create a new one for a larger maximum ALGO stake.
        Moreover, most node runners offer to notify you (one or multiple times) if your stake increases above the agreed limits.
        Only if you don't act, will your service contract be terminated.

      </span>
    ),
  },
  {
    ques: "When does staking effectively begin?",
    ans: (
      <span>
        The Algorand {gls("consensus")} operates with a 320-round delay with regards to {gls("consensus")} participation (i.e. staking).
        Thus you will effectively start staking and potentially receiving staking rewards after the participation keys step into validity and after this delay has passed.
        The mentioned delay relates to roughly 15 minutes.

      </span>
    ),
  },
  {
    ques: "What if the node runner does not set up the node for me after I pay for the service?",
    ans: (
      <span>
        Part of the node runner service terms is the so&#8209;called setup time.
        This is the maximum amount of time that the node runner may take to set up the node for you.
        You can reclaim the paid fee in full if the node runner does not set up the node for you in this time.

      </span>
    ),
  },
  {
    ques: "What if the node runner does not operate the node well?",
    ans: (
      <span>
        There is no slashing on Algorand, meaning you cannot lose funds due to {gls("staking")}, unlike with the majority of other blockchains.
        If the node runner does not operate the node well, you will only be missing out on the network's {gls("staking rewards")}.
        If the network notices that the node runner is underperforming, the contract can be automatically terminated and the remainder of your unspent operational fee returned to you.

      </span>
    ),
  },
  {
    ques: "What if the node runner incorrectly prepares the node for me?",
    ans: (
      <span>
        If the node has been incorrectly prepared for you, the same will happen as if the node is not being correctly operated.

      </span>
    ),
  },
  {
    ques: "Can I monitor how well is the service being performed?",
    ans: (
      <span>
        By using off&#8209;chain performance monitoring services like <LinkExt href="https://alerts.allo.info/" children="https://alerts.allo.info/" className={faqLinkStyle}/> it is possible to see how the node is performing.
        If such monitoring services notice possible underperformance, you can withdraw from the contract.

      </span>
    ),
  },
  {
    ques: "Can I cancel my contract?",
    ans: (
      <span>
        Yes, you can cancel an active contract at any point in time!
        You get automatically returned the portion of the operational fee that corresponds to the duration that you have not yet used.

      </span>
    ),
  },
  {
    ques: "Can I extend or renew my contract?",
    ans: (
      <span>
        Yes, you simply conclude a new contract with the same node runner for a new duration and maximum stake!
        Note that if the node runner updated their terms of use, the new terms will apply for the new contract.

      </span>
    ),
  },
  {
    ques: "Can the node runner change the terms of an active contract?",
    ans: (
      <span>
        No. Once the contract is concluded, all terms are fixed for the duration of the contract.

      </span>
    ),
  },
  {
    ques: "Can I deregister my participation keys without going to Valar?",
    ans: (
      <span>
        Yes. You can deregister your participation keys at anytime, even without withdrawing from the concluded contract.
        To get any unspent portion of the operational fee, you can withdraw from the contract at a later point.
        If you do not withdraw from the contract, you can even register the same participation keys again.

      </span>
    ),
  },
  {
    ques: "Why do I have to pay 2 ALGO fee during key registration transaction?",
    ans: (
      <span>
        The {gls("Algorand")} network requires a higher fee to opt in {glspl("account")} to be tracked by {gls("Algorand")} network's performance monitoring mechanism.
        Without being opted into the network's performance tracking, you cannot stake via Valar.
        Being opted into the performance tracking is a condition by the network to be eligible for {gls("staking rewards")}.

      </span>
    ),
  },
  {
    ques: "Are there smart contracts involved when using Valar?",
    ans: (
      <span>
        Yes, there are.
        These smart contracts are used just for processing the payment for the staking service of the node runner.
        Your ALGO always stays in your wallet and are not exposed to any smart contract risks.

      </span>
    ),
  },
  {
    ques: "Where can I see all my exact contract terms?",
    ans: (
      <span>
        All the terms are defined in the smart contracts that get created when you conclude a contract for the staking service with the node runner.
        You can check the Valar open-source smart contract to understand the exact details.

      </span>
    ),
  },
  {
    ques: "What assets can be used via Valar to pay the node runners?",
    ans: (
      <span>
        Node runners select in which asset they will be accepting the payments for their service.
        They can choose among the assets supported by the Valar platform.
        Currently, the supported asset is USDC (ASA ID 31566704 on {gls("Algorand")} Mainnet).

      </span>
    ),
  },
  {
    ques: "What are the notification messages I am getting from Valar?",
    ans: (
      <div>
        The Valar Platform automatically notifies you when your contract's state changes.
        The notification message is sent in the note field of a zero-payment transaction issued by the Valar Platform smart contracts.
        All messages begin with "Message from Valar:" and are sent by the main Valar Platform smart contract.
        Possible messages are:

        Yes! Your ALGO is completely unlocked and in your sole custody at all times. You can spend it or get more ALGO.
        Your stake will be automatically updated by the {gls("Algorand")} network.
        It is important to note that that
        <ul className="ml-5 list-disc">
          <li>
            <div className="italic">Node has been prepared for you to stake.</div>
            The node for your new contract is now ready.
            You can go to Valar website to confirm the step.
          </li>
          <li>
            <div className="italic">Node runner has unfortunately not prepared a node for you.</div>
            The node for your new contract has not been prepared for you in the agreed time.
            Your full payment can be reclaimed.
          </li>
          <li>
            <div className="italic">You have not confirmed the node that was prepared for you.</div>
            You did not confirm in the agreed amount of time the setup that the node runner prepared for you.
            The contract has thus been canceled.
          </li>
          <li>
            <div className="italic">Your contract to stake with a node runner has ended.</div>
            Your contract for staking has expired.
            You do not stake anymore.
            You can conclude new contract to continue staking.
          </li>
          <li>
            <div className="italic">Your balance is outside the limits agreed with the node runner. Correct it!</div>
            Your account is breaching one or multiple terms regarding its balance, i.e. your ALGO balance is larger than the agreed maximum stake and/or you do not meet the node runner's eligibility requirements by holding sufficient amounts of the agreed ASAs.
            You can go to Valar website to check your contract details that you agreed with.
            If you do not correct your balance to the agreed amounts, your contract can get terminated and you will stop staking.
            You can also withdraw from the current contract and conclude a new one with terms suitable to your current balances.
          </li>
          <li>
            <div className="italic">Your contract has ended because you breached the terms too many times.</div>
            Your account has breached one or multiple times the terms regarding its balance, i.e. your ALGO balance was larger than the agreed maximum stake and/or you did not meet the node runner's eligibility requirements by holding sufficient amounts of the agreed ASAs.
            You do not stake anymore.
            You can conclude a new contract to start staking again.
          </li>
          <li>
            <div className="italic">The network has suspended your account from staking. You don't stake anymore.</div>
            The Algorand network has determined that your account has not been responding as expected.
            You do not stake anymore.
            The reason for this could be the node runner not operating the node sufficiently well, or if you did not sign the correct participation keys or have closed out your account.
            You can conclude a new contract to start staking again.
          </li>

          <li>
            <div className="italic">There is an issue with your payment to the node runner. You don't stake anymore.</div>
            The payment of the node runner fees you have made when concluding the contract has been blocked.
            This is a breach in contract terms.
            You do not stake anymore.
            The issue with the payment can happen if the ASA issuer has frozen or clawed back your payment.
            You should speak with the asset issuer regarding what has happened.
          </li>
          <li>
            <div className="italic">Your contract to stake with a node runner is expiring. Consider extending it!</div>
            Your current service contract is about to expire.
            When the contract expires, you will stop staking.
            This is a reminder that you can extend your contract to continue staking with the same node runner.
            You can also select a different node runner after contract expiry or if you withdraw from the contract early.
          </li>
        </ul>
      </div>
    ),
  },
  {
    ques: "Is my identity revealed when I stake?",
    ans: (
      <span>
        No information is collected or shared when you stake via the Valar Platform.
        All communication for staking happens through the {gls("Algorand")} blockchain. Some node runners might accept only users who disclose their information (KYCed users) for regulatory reasons.

      </span>
    ),
  },
  {
    ques: "The countdown timer for setup/confirmation/expiration of the contract strangely skipped a beat. Why is that?",
    ans: (
      <span>
        Blockchains do not have a precise notion of time.
        The time in blockchains is measured in blocks, which are also called rounds.
        While blocks are normally produced in very consistent time steps, they can vary.
        All timings on the platform are estimations based on the average block time intervals.
        All the contract terms are defined based on blockchain rounds and all inputs from the Valar UI get converted to round numbers based on the average block time interval.

      </span>
    ),
  },
  {
    ques: "How does Valar work?",
    ans: (
      <span>
        The Valar platform simply facilitates peer-to-peer staking by acting as a decentralized marketplace where {gls("Algorand")} users can easily find and start staking with node runners around the globe.
        Anyone is free to join.
        The platform consists of three types of smart contracts: Noticeboard, Validator Ad, and Delegator Contract.
        As the name suggests, the Noticeboard serves as a public, completely decentralized Noticeboard, where node runners can put up advertisements (i.e. Validator Ad) for their staking services and define the corresponding service terms.
        When an {gls("Algorand")} user agrees with the advertised terms and wants to start staking with the node runner, a Delegator Contract is created.
        The contract defines all the terms of the service, including payment obligations.
        When the node runner sees the newly created Delegator Contract, it generates the participation keys for the user and submits them to the Delegator Contract.
        When the user sees this, they can simply sign the generated participation keys, at which point they start {gls("staking")}.

      </span>
    ),
  },
  {
    ques: "How is Valar different from liquid staking of Folks Finance, Tinyman, or CompX?",
    ans: (
      <span>
        Compared to liquid staking solutions, with Valar's peer-to-peer staking your ALGO never leave your wallet.
        It enables a larger network decentralization since funds are not aggregated in accounts managed by a central authority.
        This leads to higher protection of your assets and all other assets on the network.
        With a larger decentralization, you empower solutions that rely on the {gls("Algorand")} network.
        Moreover, Valar provides transparent and fixed costs for the staking. You pay for the service in advance and even in stablecoins.
        Because your ALGO stay in your wallet at all times you can directly spend them whenever you like, unlike with liquid staking where you first have to convert the liquid staking token back to ALGO.
        Exchanges of assets can have different implications in different jurisdictions.
        With Valar you stake all the ALGO that is in your wallet, even any ALGO that is locked in it as part of wallet's minimum balance requirement.
        Your {gls("account")} will also be able to directly participate in the Algorand's xGov governance program.

      </span>
    ),
  },
  {
    ques: "How is Valar different from Reti Pools?",
    ans: (
      <span>
        Compared to staking pools solutions, with Valar's peer-to-peer staking your ALGO never leave your wallet.
        It enables a larger network decentralization since funds are not aggregated in an account managed by a central authority.
        This leads to higher protection of your assets and all other assets on the network.
        With a larger decentralization, you empower solutions that rely on the {gls("Algorand")} network.
        Moreover, Valar provides transparent and fixed costs for the staking. You pay for the service in advance and even in stablecoins.
        Because your ALGO stay in your wallet at all times you can directly spend them whenever you like, unlike with staking pools where you first have to withdraw your ALGO from the pool.
        Transaction of assets can have different implications in different jurisdictions.
        With Valar you stake all the ALGO that is in your wallet, even any ALGO that is locked in it as part of wallet's minimum balance requirement.
        Your {gls("account")} will also be able to directly participate in the Algorand's xGov governance program.
      </span>
    ),
  },
];

const ValidatorFAQs: FAQ[] = [
  {
    ques: "Why run a node?",
    ans: (
      <span>
        If you run your own node, you can not only stake by yourself and reap staking rewards, but you can also generate additional income by letting others stake on your node with Valar.
        Moreover, your node further increases network decentralization, increasing network security and resilience for everyone.

      </span>
    ),
  },
  {
    ques: "How can I become a node runner?",
    ans: (
      <span>
        See our <LinkExt
          href={"/learn-node"}
          children={"guide"}
          className={"text-secondary"}
        /> {" "}
        on how to become a node runner and offer your node running services via Valar.
      </span>
    ),
  },
  {
    ques: "I am running a node. How can I benefit from Valar?",
    ans: (
      <span>
        If you are already running a node, you likely have the capacity to stake for more than just one account.
        With Valar, you can let others stake on your node in return for the fees that you define for this service.
        Not only that, you help secure the network by bringing more ALGO stake online.

      </span>
    ),
  },
  {
    ques: "How can I join Valar as a node runner?",
    ans: (
      <span>
        After you have a node up and running, create an ad on Valar for your node running service and run the Valar Daemon.

      </span>
    ),
  },
  {
    ques: "What are Valar fees for node runners?",
    ans: (
      <span>
        The Valar Platform takes a 10% commission on the revenue generated by the node runners.
        Moreover, the Valar Platform charges a one&#8209;time registration fee of 5 ALGO for each node runner.
        Furthermore, the Valar Platform charges a one-time ad creation fee of 5 ALGO for each ad.
        The one-time fees serve as an anti&#8209;spam mechanism to not overwhelm the Valar Platform and its users with spam node runners and ads.

      </span>
    ),
  },
  {
    ques: "How can I setup an ad for my node?",
    ans: (
      <span>
        To setup an ad for your node, you have to define the terms of your service.

        This includes defining your fees.
        These consist of a setup fee - a one&#8209;time cost for preparing the node for new user, and an operational fee, which is charged to the user according to their requested duration of staking.
        You can define the operational fee as a flat fee and/or to be proportional to the user's requested maximum stake because of the potential additional burden on your node due to the higher stake.
        You also select the currency of the fee payment.

        As a responsible node runner, you can set the maximum limits on the ALGO amount that a user can stake on your node.
        This way you can reject accepting larger stakes than your node can responsibly handle.
        If a user stakes more than the agreed limit, the service contract can get terminated.

        Because users can involuntarily get their stakes increased above the agreed maximum as sending ALGO is permissionless, you can give them a certain number of warnings before terminating the contract due to the breached limits.
        In case you charge according to the user's requested maximum stake, you can give them a buffer on top of their requested maximum stake so they are less likely to breach the limit.

        You also set the time until when the users can stake with you as well as the minimum and maximum duration of staking.
        Moreover, you define the setup time - the time in which you promise to respond to a user's request to stake via your node by generating and giving them the participation keys; and the confirmation time - the time in which the user should sign the generated keys and confirm the service contract.

        In order to automatically service the user staking request via this ad, you must define a manager address.
        It is recommended to use the Valar Daemon for managing the requests.
        As part of the ad management, you must also define how many users you can accept on the node.

      </span>
    ),
  },
  {
    ques: "I don't want everyone to stake on my node. Is it possible to limit access?",
    ans: (
      <span>
        Yes! Whether you want to offer your node just to your family, friends, community, or users that you know (KYCed users) to meet your regulatory requirements, the process is the same.
        In your ad terms, just simply define what assets and in what amounts the users of your node must have to be eligible to stake with you.
        Users without these assets will not be able to stake with you.
        If they do not meet the eligibility anymore after starting a service contract with you, the contract can get terminated.

      </span>
    ),
  },
  {
    ques: "Can I modify my ad?",
    ans: (
      <span>
        Yes! You can modify your ad at any point in time.
        However, the new changes will apply only for future service contracts.
        The terms of any active contract cannot be changed.

      </span>
    ),
  },
  {
    ques: "Which payment currencies are supported?",
    ans: (
      <span>
        The node runner defines in their ad in which asset they will be accepting the payments for their service.
        They can choose among the assets supported at the Valar Platform.
        Currently, the supported asset is USDC (ASA ID 31566704 on {gls("Algorand")} Mainnet).
        Each ad can be configured to accept payments only in one currency at a time.

      </span>
    ),
  },
  {
    ques: "What if the payment currency can be frozen or clawed back -- what happens to active contracts if the payment is frozen or clawed back?",
    ans: (
      <span>
        There is a strict separation of assets thanks to the three types of smart contracts used by the Valar Platform.
        When a payment for the service happens, the funds are atomically routed via the Noticeboard to the Validator Ad and then finally to the Delegator Contract.
        If at the time of payment, any of these contract {glspl("address")} are frozen for whatever reason by the asset's issuer, the payment will fail.
        The result will be that the creation of a new contract will be rejected and no funds will have been transferred.

        Once a contract has been concluded, and thus paid for, the node runner can claim the portion of the fees for the already provided service.
        When the claiming of the earned fee is made, the portion of the payment is transferred from the Delegator Contract to the Validator Ad.
        If at the time of the claiming, the Validator Ad {gls("address")} is frozen for whatever reason by the asset's issuer, the payment will not be made and the corresponding fees forfeited. It is up to the node runner to discuss any compensation for this with the asset issuer.
        Any amounts of failed payments will be reclaimed by the {gls("delegator")} at the end of the contract.

        Similarly, if at the time of the claiming, the Delegator Contract {gls("address")} is frozen for whatever reason by the asset's issuer, the payment will not be made.
        The node runner will in this case be able to claim that the {gls("delegator")} has breached the agreed contract payment terms because it was not able to pay the service.
        When a payment breach is reported, the contract is terminated.
        It is up to the {gls("delegator")} to discuss any compensation for the consequences of this action with the asset issuer.
        The same payment breach occurs if the payment has been clawed back from the Delegator Contract for whatever reason by the asset's issuer.

      </span>
    ),
  },
  {
    ques: "Can the Valar Platform increase its fees?",
    ans: (
      <span>
        While the Valar Platform can change its fees, this does not have an influence on any active service contracts.
        Moreover, changes in the one-time payments fees do not have an influence on already registered node runners or created ads.
        Any changes in the Valar Platform's commission have to be accepted by the node runner before they take affect on any new service contracts.

      </span>
    ),
  },
  {
    ques: "What if I have more nodes?",
    ans: (
      <span>
        You can define up to 110 ads under one node runner {gls("account")}.

      </span>
    ),
  },
  {
    ques: "Can I stay anonymous while offering the node running service?",
    ans: (
      <span>
        Yes. No information is collected or shared when you offer the node running service via the Valar Platform.
        All communication for staking happens through the {gls("Algorand")} blockchain.
        Note however that user might not trust anonymous node runners to do good for the network.
        Also note that due to regulatory reasons, different user interface might not show unknown node runners to users.

      </span>
    ),
  },
  {
    ques: "How to configure the Valar Daemon?",
    ans: (
      <span>
        The Valar Daemon is initialized according to a configuration file when it is run. The configuration file requires you to enter the mnemonic of the Validator Manager (the {gls("hot wallet")}) and the IDs of the validator ads that the Valar Daemon should service.
        Additionally, you can configure the Valar Daemon to run on an alternative network for testing purposes, adjust the level of information it provides during execution, and change the period at which it checks and manages service contracts.
        Click <LinkExt href="/learn-node" children="here" className={faqLinkStyle}/> for more information on downloading, setting up, and running the Valar Daemon.
      </span>
    ),
  },
  {
    ques: "What if a Delegator does not sign the submitted keys or changes them later?",
    ans: (
      <span>
        The service contract remains valid.
        The node runner is still getting paid for the provided service even if it is not being used.
        However, the contract can get terminated if the {gls("delegator")} is removed from consensus by the {gls("Algorand")} network because the keys they are currently using are not performing as expected.

      </span>
    ),
  },
  {
    ques: "What if a Delegator closes out their account?",
    ans: (
      <span>
        The contract can then get terminated because the account is not tracked anymore by the {gls("Algorand")} network's performance monitoring mechanism.

      </span>
    ),
  },
  {
    ques: "Who can become a node runner?",
    ans: (
      <span>
        Anyone can become a node runner since Algorand is a completely permissionless blockchain.
        You simply need a node and run the {gls("Algorand daemon")}, 24 hours a day, 7 days a week, 365 days a year.

      </span>
    ),
  },
  {
    ques: "What are the duties of node runners?",
    ans: (
      <span>
        Node runners are the backbone of the {gls("Algorand")} blockchain.
        For its seamless operation, the node runners must ensure good node performance and act in good faith towards the network by correctly validating blocks as well as by keeping up-to-date with the protocol changes.
        In case a node runner acts maliciously, their reputation and any assets on the network are at risk.
      </span>
    ),
  },
];


const AlgorandFAQs: FAQ[] = [
  {
    ques: "What is Algorand?",
    ans: (
      <span>
        Algorand is a modern, high&#8209;performance, and energy&#8209;efficient single&#8209;layer blockchain.
        It is quantum&#8209;secure, with instant finality, short round times (below 3 s), consistently high throughput (10k transactions per second), reliability (continuously operating since 2019), and low fees (below 0.001 USD per transaction).
        Among blockchains, it stands out with its high decentralization potential due to the low computational resources required to operate a node, while having high computational precision and execution thanks to its {gls("Algorand")} Virtual Machine.

      </span>
    ),
  },
  {
    ques: "Who is an Algorand user?",
    ans: (
      <span>
        Anybody who owns ALGO and uses the {gls("Algorand")} network.

      </span>
    ),
  },
  {
    ques: "Who can become an Algorand user?",
    ans: (
      <span>
        Algorand is a completely permissionless blockchain.
        Anyone can you use it.
        You might already be an {gls("Algorand")} user without even knowing if you have been flying in South America with the Flybondi airline or a collector of FIFA's collection of iconic moments.

      </span>
    ),
  },
  {
    ques: "How to become an Algorand user?",
    ans: (
      <span>
        Simply acquire some ALGO to pay for your transactions.
        You can acquire ALGO at centralized exchanges like Coinbase or Kraken, or directly with blockchain wallets for {gls("Algorand")} like Pera or Defly wallets.

      </span>
    ),
  },
  {
    ques: "Who is a node runner?",
    ans: (
      <span>
        Node runner is someone who runs a node with the {gls("Algorand daemon")}, 24 hours a day, 7 days a week, 365 days a year.

      </span>
    ),
  },
  {
    ques: "Who can become a node runner?",
    ans: (
      <span>
        Algorand is a completely permissionless blockchain.
        Anyone can become a node runner by running the {gls("Algorand daemon")}.

      </span>
    ),
  },
  {
    ques: "How to become a node runner?",
    ans: (
      <span>
        See our detailed guide on how to become a node runner and offer your node running services via Valar.

      </span>
    ),
  },
  {
    ques: "What is the difference between an Algorand user and a node runner?",
    ans: (
      <span>
        An Algorand user is anyone who simply owns some ALGO.
        Node runners are mostly tech-savvy people who are running one or multiple nodes, 24 hours a day, 7 days a week, 365 days a year.
        A person can be both an {gls("Algorand")} user and a node runner simultaneously.

      </span>
    ),
  },
  {
    ques: "What is Algorand deposit?",
    ans: (
      <span>
        {gls("Algorand")} network pricing model consists of two parts: 1) ALGO fees to pay for user transactions, and 2) an ALGO deposit to store user's data, also known as Minimum Balance Requirement (MBR).
        The MBR is locked in the user's {gls("account")} while the user is using the storage.
        When a user stops using the {gls("Algorand")} network's storage, the deposit is unlocked.

      </span>
    ),
  },
];

const FAQs = {
  stake: {
    heading: "About Staking",
    faqs: StakingFAQs,
  },
  delegator: {
    heading: "Staking with Valar",
    faqs: DelegatorFAQs,
  },
  validator: {
    heading: "Node Running with Valar",
    faqs: ValidatorFAQs,
  },
  algo: {
    heading: "About Algorand",
    faqs: AlgorandFAQs,
  },
};

const socials = [
  {
    icon: telegram,
    link: telegramLink,
  },
  {
    icon: discord,
    link: discordLink,
  },
  {
    icon: email,
    link: emailLink,
  },
  {
    icon: linkedIn,
    link: linkedInLink,
  },
];

const FaqPage = () => {
  const [currFAQ, setCurrFAQ] = useState<"stake" | "delegator" | "validator" | "algo">("stake");

  return (
    <Container>
      <div className="px-2 py-4 lg:px-20">
        <h1 className="text-3xl font-semibold">FAQ</h1>
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-4">
          <div className="col-span-1 lg:mr-16">
            <div className="mb-8 flex flex-col gap-6 text-secondary">
              <h2
                className="cursor-pointer"
                onClick={() => setCurrFAQ("stake")}
              >
                About Staking
              </h2>
              <h2
                className="cursor-pointer"
                onClick={() => setCurrFAQ("delegator")}
              >
                Staking with Valar
              </h2>
              <h2
                className="cursor-pointer"
                onClick={() => setCurrFAQ("validator")}
              >
                Node Running with Valar
              </h2>
              <h2 className="cursor-pointer" onClick={() => setCurrFAQ("algo")}>
                About Algorand
              </h2>
            </div>
            <Separator className="my-6 bg-white bg-opacity-15" />
            <div>
              <div className="text-sm">
                Have an issue and can't find the answer here? Let us know
                through any of our social media.
              </div>
              <div className="mb-8 mt-4 flex items-center justify-between gap-2 px-10 lg:mb-0 lg:px-0">
                {socials.map((item, index) => (
                  <a href={item.link} key={index} target="blank_">
                    <img src={item.icon} className="h-6 w-6" />
                  </a>
                ))}
              </div>
            </div>
          </div>
          <div className="col-span-3">
            <div className="border-b border-white border-opacity-15 pb-2">
              <h1 className="text-lg">{FAQs[currFAQ].heading}</h1>
            </div>
            <Accordion type="single" collapsible className="w-full">
              {FAQs[currFAQ].faqs.map((faq, index) => (
                <AccordionItem key={index} value={`item-${index}`}>
                  <AccordionTrigger className="text-base">
                    {faq.ques}
                  </AccordionTrigger>
                  <AccordionContent className="text-base leading-7">
                    {faq.ans}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </div>
      </div>
    </Container>
  );
};

export default FaqPage;
