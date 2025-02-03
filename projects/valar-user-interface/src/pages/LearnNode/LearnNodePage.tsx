import { Button } from "@/components/ui/button";
import LinkExt from "@/components/ui/link-ext";
import { Separator } from "@/components/ui/separator";
import { ROLE_VAL_STR } from "@/constants/smart-contracts";
import { useNavigate } from "react-router-dom";

const codeStyle = "px-0.5 py-0 rounded text-sm text-tertiary-light whitespace-nowrap bg-background-light";

const LearnNodePage = () => {
  const navigate = useNavigate();

  return (
    <div className="flex w-full justify-center">
      <div className="max-w-[640px] px-2">
        <h1 className="font-semibold text-lg">How to run a node?</h1>
        <Separator className="my-2" />
        <p className="text-sm">
          Follow the guide below to learn how to set up and run a node. If you
          already have one, see below on how
          to automatically serve users that want to stake on your node.
        </p>
        <div className="mt-4 flex flex-col gap-6">
          <div className="space-y-2">
            <h3>Step 1 - Check your computer</h3>
            <p className="text-sm">
              To run a node yourself, you will need a computer that is
              continuously running - 24 hours a day, 7 days a week, 365 days a
              year.
              Check computer requirements at {" "}
              <LinkExt
                href={"https://developer.algorand.org/docs/run-a-node/setup/install/#hardware-requirements"}
                children={"Algorand's developer docs"}
                className={"text-secondary"}
              />.
            </p>
          </div>
          <div className="space-y-2">
            <h3>Step 2 - Install Algorand node</h3>
            <p className="flex flex-col gap-1 text-sm">
              Install the node using, e.g.:
              <ul className="ml-5 list-disc space-y-1 mt-1">
                <li>
                  Applications with a graphical user interface (GUI) such as{" "}
                  <LinkExt
                    href={"https://func.algo.xyz/"}
                    children={"Funk's Ultimate Node Controller (FUNC)"}
                    className={"text-secondary"}
                  />
                  {" "}or{" "}
                  <LinkExt
                    href={"https://github.com/AustP/austs-one-click-node/releases"}
                    children={"Aust One-Click Node (A1CN)"}
                    className={"text-secondary"}
                  />
                </li>
                <li>
                  The command-line one-stop-shop for Algorand node running{" "}
                  <LinkExt
                    href={"https://github.com/algorandfoundation/nodekit"}
                    children={"NodeKit"}
                    className={"text-secondary"}
                  />
                </li>
                <li>
                  A custom install with more flexibility according to{" "}
                  <LinkExt
                    href={"https://developer.algorand.org/docs/run-a-node/setup/install/"}
                    children={"Algorand's developer guide"}
                    className={"text-secondary"}
                  />
                </li>
              </ul>

              It is recommended that you enable automatic running of the node on startup since your machine may reboot unexpectedly, e.g. due to interrupted power supply.
              The configuration of automatic startup varies between systems and installation approaches.
              Check the specific guide that you followed for node installation for more details.

            </p>
          </div>
          <div className="space-y-2">
            <h3>Step 3 - Monitor your node</h3>
            <p className="text-sm">
              There are multiple ways to monitor your node.
              For example, you can enable (anonymous) node telemetry to send important events, errors, and metrics to a chosen telemetry service like Nodely or Algorand Technologies.
              You can follow {" "}
              <LinkExt
                href="https://nodely.io/docs/telemetry/quickstart/"
                children="Nodely's guide"
                className={"text-secondary"}
              />
              {" "}or{" "}
              <LinkExt
                href={"https://developer.algorand.org/docs/run-a-node/setup/install/#configure-telemetry"}
                children={"Algorand's developer docs"}
                className={"text-secondary"}
              />.
            </p>
            <p className="text-sm">
              You can also monitor directly the performance of accounts that stake on your node.
              For this, you can use services like <LinkExt href="https://alerts.allo.info/" children="https://alerts.allo.info/" className={"text-secondary"}/>.
            </p>
          </div>
        </div>
        <div className="mt-8">
          <h1 className="font-semibold text-lg">How to automatically serve users' staking requests?</h1>
          <Separator className="mt-3" />
          <div className="flex flex-col gap-3">
            <p className="mt-3 text-sm">
              As a node runner on the Valar Platform, you will be receiving staking requests in the form of new Delegator Contracts.
              Each of these requires the generation of participation keys, monitoring to check that the contract's terms are met, and cleanup in case of an early ending.
              The Valar Daemon automates these tasks for you.
            </p>
            <p className="text-sm">
              Follow the below steps for quickly setting up the Valar Daemon or review the package information on {" "}
              <LinkExt
                href={"https://pypi.org/project/valar_daemon/"}
                children={"PyPI"}
                className={"text-secondary"}
              />{" "}for more details.
            </p>
            <div className="flex flex-col gap-2 pb-3">
              <h3>Step 1 - Install</h3>
              <p className="text-sm">
                Ensure that your node has Python 3.12 or greater, then install the Valar Daemon using {" "}
                <code className={codeStyle}>pip install valar_daemon</code>.
              </p>
            </div>
            <div className="flex flex-col gap-2 pb-3">
              <h3>Step 2 - Configure</h3>
              <p className="text-sm">
                To configure the Valar Daemon:
                <ul className="ml-5 list-disc space-y-1 mt-1">
                  <li>
                    Make a directory named <code className={codeStyle}>valar-daemon</code>
                  </li>
                  <li>
                    Create an empty file <code className={codeStyle}>daemon.config</code> in <code className={codeStyle}>valar-daemon</code>
                  </li>
                  <li>
                    Copy the contents of <LinkExt
                      href={"https://github.com/ValarStaking/valar/tree/master/projects/valar-daemon/daemon.config"}
                      children={"https://github.com/ValarStaking/valar/tree/master/projects/valar-daemon/daemon.config"}
                      className={"text-secondary"}
                    /> {" "}to <code className={codeStyle}>daemon.config</code>
                  </li>
                  <li>
                    Overwrite the following fields in <code className={codeStyle}>daemon.config</code>:
                    <ul className="ml-5 list-disc space-y-1 mt-1">
                      <li>
                        The ID of your ad: <code className={codeStyle}>validator_ad_id_list = [9876543210]</code>
                      </li>
                      <li>
                        The mnemonic of your Validator Manager (hot wallet): <code className={codeStyle}>validator_manager_mnemonic = protect security network ... able reward</code>
                      </li>
                      <li>
                        <p>
                          The URL and port of Algod running on your node: <code className={codeStyle}>algod_config_server = http://localhost:8080</code>.
                        </p>
                        <p>
                          You can find this in your node's files, for example, usually under <code className={codeStyle}>var/lin/algorand/algo.net</code> for Linux users.
                        </p>
                      </li>
                      <li>
                        <p>
                        The admin API token to access Algod on your node: <code className={codeStyle}>algod_config_token = aaaaaa...aaaaaa</code>
                        </p>
                        <p>
                          You can find this in your node's files, for example, usually under <code className={codeStyle}>var/lin/algorand/algo.admin.token</code> for Linux users.
                        </p>
                      </li>
                    </ul>
                  </li>
                </ul>
              </p>
            </div>
            <div className="flex flex-col gap-2 pb-3">
              <h3>Step 3 - Run</h3>
              <p className="text-sm">
                Run the Valar Daemon using <code className={codeStyle}>python -m valar_daemon.run_daemon</code>
              </p>
              <p className="text-sm">
                This will service the Validator Ad, indicated in <code className={codeStyle}>daemon.config</code>, and all the associated Delegator Contracts.
                You can check in on the Valar Daemon through the real-time logs in the automatically generated <code className={codeStyle}>valar-daemon-log</code> directory.
                View the Valar Daemon package information on {" "}
                <LinkExt
                  href={"https://pypi.org/project/valar_daemon/"}
                  children={"PyPI"}
                  className={"text-secondary"}
                />{" "} for more information about the logs, running the Valar Daemon in the background, and other options.
              </p>
            </div>
          </div>
        </div>
        <Button variant={"v_primary"} className="my-10" onClick={() => navigate("/dashboard",  { state: { role: ROLE_VAL_STR }})}>
          To Node Runner Dashboard
        </Button>
      </div>
    </div>
  );
};

export default LearnNodePage;
