import { BOX_PARTNERS_PREFIX } from '@/constants/smart-contracts'
import { BoxExistsResponse, BoxUtils } from '@/utils/contract/box-utils'
import { ABIAddressType, ABITupleType, ABIUintType } from 'algosdk'
import AlgodClient from 'algosdk/dist/types/client/v2/algod/algod'

export class PartnerInfo {
  address: string
  partnerCommission: bigint

  static readonly abi = new ABITupleType([new ABIUintType(64)])

  constructor(address: string, partnerCommission: bigint) {
    this.address = address
    this.partnerCommission = partnerCommission
  }

  static decodeBytes(address: string, data: Uint8Array) {
    const d = this.abi.decode(data) as [bigint]

    return new PartnerInfo(address, d[0])
  }

  static async getUserInfo(algodClient: AlgodClient, partnerAddress: string) {
    const boxRes: BoxExistsResponse = await BoxUtils.getNoticeboardBox(
      algodClient,
      new Uint8Array([...BOX_PARTNERS_PREFIX, ...new ABIAddressType().encode(partnerAddress)]),
    )
    if (!boxRes.exists) return undefined

    return PartnerInfo.decodeBytes(partnerAddress, boxRes.value)
  }
}
